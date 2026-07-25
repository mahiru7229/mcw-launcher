package org.mcwlauncher.lanagent;

import java.lang.instrument.Instrumentation;

/**
 * Minimal host-side LAN agent used by MCW Launcher.
 *
 * <p>The agent is intentionally dormant unless {@code -Dmcw.lan.offline=true}
 * is present. It does not touch Authlib, tokens, networking, or files. Its only
 * transformer targets MinecraftServer#setUsesAuthentication(boolean) and forces
 * the value written by that setter to {@code false}.</p>
 */
public final class McwLanAgent {
    static final String ENABLE_PROPERTY = "mcw.lan.offline";
    static final String TARGET_CLASS_PROPERTY = "mcw.lan.target.class";
    static final String TARGET_METHOD_PROPERTY = "mcw.lan.target.method";
    static final String DEFAULT_TARGET_CLASS = "net/minecraft/server/MinecraftServer";
    static final String DEFAULT_TARGET_METHOD = "setUsesAuthentication";

    private McwLanAgent() {
    }

    public static void premain(String agentArguments, Instrumentation instrumentation) {
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

        instrumentation.addTransformer(new LanOfflineTransformer(targetClass, targetMethod), false);
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
        System.err.println("[MCW LAN Agent] " + message);
    }
}
