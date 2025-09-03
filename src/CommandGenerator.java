
public class CommandGenerator {
    public String generateJavaCompileCommand(String file, String outputDir) {
        return "javac -d " + outputDir + " " + file;
    }
    public String generateJavaRunCommand(String mainClass, String classpath) {
        return "java -cp " + classpath + " " + mainClass;
    }
}
