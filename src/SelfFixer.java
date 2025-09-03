
public class SelfFixer {
    private static final int MAX_ATTEMPTS = 3;
    public static boolean runWithFixes(String cmd, ShellType shellType) {
        int attempt = 0;
        while (attempt < MAX_ATTEMPTS) {
            boolean success = ShellExecutor.run(cmd, shellType);
            if (success) return true;
            String fixedCmd = attemptFix(cmd);
            if (fixedCmd == null) return false;
            cmd = fixedCmd;
            attempt++;
        }
        return false;
    }
    private static String attemptFix(String cmd) {
        if (cmd.contains("javac") && !cmd.contains("-d")) return cmd + " -d bin";
        if (cmd.contains("java") && !cmd.contains("-cp")) return cmd.replace("java ", "java -cp bin ");
        return null;
    }
}
