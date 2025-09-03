
public class ShellRouter {
    public static ShellType detectPreferredShell() {
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("win")) return ShellType.POWERSHELL;
        else if (os.contains("mac") || os.contains("nix") || os.contains("nux")) return ShellType.BASH;
        return ShellType.UNKNOWN;
    }
    public static String[] getShellCommand(ShellType shell, String cmd) {
        return switch (shell) {
            case CMD -> new String[]{"cmd.exe", "/c", cmd};
            case POWERSHELL -> new String[]{"powershell.exe", "-Command", cmd};
            case GIT_BASH, BASH -> new String[]{"bash", "-c", cmd};
            default -> new String[]{"sh", "-c", cmd};
        };
    }
}
