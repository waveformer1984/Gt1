
import java.io.*;

public class ShellExecutor {
    public static boolean run(String cmd, ShellType shellType) {
        try {
            String[] command = ShellRouter.getShellCommand(shellType, cmd);
            ProcessBuilder builder = new ProcessBuilder(command);
            builder.redirectErrorStream(true);
            Process process = builder.start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println("│ " + line);
            }
            int exitCode = process.waitFor();
            return exitCode == 0;
        } catch (IOException e) {
            System.err.println("❌ Shell run failed due to an I/O error: " + e.getMessage());
            return false;
        } catch (InterruptedException e) {
            System.err.println("❌ Shell run was interrupted: " + e.getMessage());
            Thread.currentThread().interrupt(); // Restore interrupted status
            return false;
        }
    }
}
