
import java.sql.*;

public class DBHelper {
    private static final String CREATE_COMMAND_LOG_TABLE_SQL = "CREATE TABLE IF NOT EXISTS command_log (id INTEGER PRIMARY KEY, command TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)";
    private Connection conn;
    public DBHelper(String dbFile) {
        try {
            conn = DriverManager.getConnection("jdbc:sqlite:" + dbFile);
            conn.createStatement().execute(CREATE_COMMAND_LOG_TABLE_SQL);
        } catch (SQLException e) {
            System.err.println("❌ DB Error: " + e.getMessage());
        }
    }
    public void logCommand(String command) {
        try (PreparedStatement pstmt = conn.prepareStatement("INSERT INTO command_log (command) VALUES (?)")) {
            pstmt.setString(1, command);
            pstmt.executeUpdate();
        } catch (SQLException e) {
            System.err.println("⚠️ Failed to log command: " + e.getMessage());
        }
    }
}
