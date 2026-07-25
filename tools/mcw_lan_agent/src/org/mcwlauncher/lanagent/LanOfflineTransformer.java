package org.mcwlauncher.lanagent;

import java.lang.instrument.ClassFileTransformer;
import java.security.ProtectionDomain;
import java.util.concurrent.atomic.AtomicBoolean;

final class LanOfflineTransformer implements ClassFileTransformer {
    private final String targetClassName;
    private final String targetMethodName;
    private final AtomicBoolean targetSeen = new AtomicBoolean(false);
    private final AtomicBoolean patched = new AtomicBoolean(false);
    private final AtomicBoolean patchFailed = new AtomicBoolean(false);

    LanOfflineTransformer(String targetClassName, String targetMethodName) {
        this.targetClassName = targetClassName;
        this.targetMethodName = targetMethodName;
    }

    @Override
    public byte[] transform(
        ClassLoader loader,
        String className,
        Class<?> classBeingRedefined,
        ProtectionDomain protectionDomain,
        byte[] classfileBuffer
    ) {
        if (!targetClassName.equals(className) || classfileBuffer == null) {
            return null;
        }

        targetSeen.set(true);
        McwLanAgent.log("target class loaded by " + loaderName(loader) + ": " + className.replace('/', '.'));
        try {
            byte[] transformed = BooleanSetterPatcher.patch(classfileBuffer, targetMethodName);
            if (transformed == null) {
                patchFailed.set(true);
                McwLanAgent.log("target class loaded, but the expected setter bytecode was not found; leaving Minecraft unchanged");
                return null;
            }
            patched.set(true);
            McwLanAgent.log("patched " + className.replace('/', '.') + "#" + targetMethodName + "(boolean)");
            return transformed;
        } catch (RuntimeException exception) {
            patchFailed.set(true);
            McwLanAgent.log("patch failed safely: " + exception.getMessage());
            return null;
        }
    }

    String shutdownSummary() {
        if (patched.get()) {
            return "shutdown summary: LAN Offline Mode patch was applied successfully";
        }
        if (targetSeen.get() || patchFailed.get()) {
            return "shutdown summary: target class was found, but the patch was not applied; Minecraft stayed unchanged";
        }
        return "shutdown summary: target class was never loaded; the runtime class name or mapping may differ";
    }

    private static String loaderName(ClassLoader loader) {
        return loader == null ? "bootstrap loader" : loader.getClass().getName();
    }
}
