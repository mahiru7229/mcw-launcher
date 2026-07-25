package org.mcwlauncher.lanagent;

import java.io.IOException;
import java.lang.instrument.Instrumentation;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.OffsetDateTime;

/**
 * Minimal host-side LAN agent used by MCW Launcher.
 *
 * <p>The agent is intentionally dormant unless {@code -Dmcw.lan.offline=true}
 * is present. It does not touch Authlib, tokens, networking, or Minecraft
 * files. Its only transformer targets
 * MinecraftServer#setUsesAuthentication(boolean) and forces the value written
 * by that setter to {@code false}.</p>
 */
public final class McwLanAgent {
    static final String ENABLE_PROPERTY = "mcw.lan.offline";
    static final String TARGET_CLASS_PROPERTY = "mcw.lan.target.class";
    static final String TARGET_METHOD_PROPERTY = "mcw.lan.target.method";
    static final String LOG_PATH_PROPERTY = "mcw.lan.log";
    static final String DEFAULT_TARGET_CLASS = "net/minecraft/server/MinecraftServer";
    static final String DEFAULT_TARGET_METHOD = "setUsesAuthentication";
    private static final Object LOG_LOCK = new Object();
    private static boolean fileLogFailureReported;

    private McwLanAgent() {
    }

    public static void premain(String agentArguments, Instrumentation instrumentation) {
        log("premain entered; Java " + System.getProperty("java.version", "unknown"));
        if (!Boolean.getBoolean(ENABLE_PROPERTY)) {
            log("disabled; the enable property is not true");
            return;
        }

        String targetClass = normalizeClassName(System.getProperty(TARGET_CLASS_PROPERTY, DEFAULT_TARGET_CLASS));
        String targetMethod = System.getProperty(TARGET_METHOD_PROPERTY, DEFAULT_TARGET_METHOD).trim();
        if (!isSafeMinecraftTarget(targetClass, targetMethod)) {
            log("refused unsafe target configuration");
            return;
        }

        final LanOfflineTransformer transformer = new LanOfflineTransformer(targetClass, targetMethod);
        instrumentation.addTransformer(transformer, false);
        Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {
            @Override
            public void run() {
                log(transformer.shutdownSummary());
            }
        }, "mcw-lan-agent-summary"));
        log("enabled for " + targetClass.replace('/', '.') + "#" + targetMethod + "(boolean)");
    }

    static String normalizeClassName(String value) {
        return value == null ? "" : value.trim().replace('.', '/');
    }

    static boolean isSafeMinecraftTarget(String className, String methodName) {
        return className.startsWith("net/minecraft/")
            && className.length() <= 240
            && methodName.matches("[A-Za-z_$][A-Za-z0-9_$]{0,127}");
    }

    static void log(String message) {
        String line = OffsetDateTime.now() + " [MCW LAN Agent] " + message;
        System.err.println(line);

        String configuredPath = System.getProperty(LOG_PATH_PROPERTY, "").trim();
        if (configuredPath.isEmpty()) {
            return;
        }

        synchronized (LOG_LOCK) {
            try {
                Path path = Paths.get(configuredPath).toAbsolutePath().normalize();
                Path parent = path.getParent();
                if (parent != null) {
                    Files.createDirectories(parent);
                }
                Files.write(
                    path,
                    (line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8),
                    StandardOpenOption.CREATE,
                    StandardOpenOption.APPEND
                );
            } catch (IOException | RuntimeException exception) {
                if (!fileLogFailureReported) {
                    fileLogFailureReported = true;
                    System.err.println("[MCW LAN Agent] could not write the dedicated log: " + exception.getMessage());
                }
            }
        }
    }
}
