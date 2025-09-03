
import java.util.Scanner;

public class CommandREPL {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        CommandGenerator generator = new CommandGenerator();
        ShellType shellType = ShellRouter.detectPreferredShell();
        SpeechEngine tts = new SpeechEngine();
        DBHelper db = new DBHelper("hydi_virtual.db");
        LanguageManager languageManager = new LanguageManager();

        System.out.println("🧠 Hydi REPL: Self-Healing, Multilingual, Multi-Shell");
        
        while (true) {
            System.out.print("💬 > ");
            String rawInput = scanner.nextLine();

            if (rawInput.equalsIgnoreCase("exit")) break;
            if (rawInput.startsWith("lang ")) {
                languageManager.setLanguage(rawInput.substring(5));
                continue;
            }

            String command = rawInput;
            db.logCommand(rawInput);
            tts.speak("Running command: " + rawInput);
            SelfFixer.runWithFixes(command, shellType);
        }
    }
}
