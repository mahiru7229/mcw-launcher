package org.mcwlauncher.lanagent;

import java.lang.instrument.ClassFileTransformer;
import java.security.ProtectionDomain;

final class LanOfflineTransformer implements ClassFileTransformer {
    private final String targetClassName;
    private final String targetMethodName;

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

        try {
            byte[] transformed = BooleanSetterPatcher.patch(classfileBuffer, targetMethodName);
            if (transformed == null) {
                McwLanAgent.log("target class loaded, but the expected setter bytecode was not found; leaving Minecraft unchanged");
                return null;
            }
            McwLanAgent.log("patched " + className.replace('/', '.') + "#" + targetMethodName + "(boolean)");
            return transformed;
        } catch (RuntimeException exception) {
            McwLanAgent.log("patch failed safely: " + exception.getMessage());
            return null;
        }
    }
}
