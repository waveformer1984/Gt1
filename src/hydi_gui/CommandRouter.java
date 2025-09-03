package hydi_gui;

public class CommandRouter {

    public static String detectShell() {
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("win")) {
            return "powershell"; // or "cmd"
        } else if (os.contains("nix") || os.contains("nux")) {
            return "bash";
        } else {
            return "unknown";
        }
    }

    public static String formatCommand(String rawCommand) {
        // Placeholder for future routing enhancements
        return rawCommand;
    }
}
