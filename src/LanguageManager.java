
public class LanguageManager {
    private String lang = "java";
    public void setLanguage(String l) {
        this.lang = l;
        System.out.println("🔧 Code language set to: " + l);
    }
    public String getLanguage() {
        return lang;
    }
}
