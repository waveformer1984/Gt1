package hydi_gui;

import javafx.scene.control.Label;
import javafx.scene.layout.*;
import javafx.scene.input.*;

public class CommandBlockPane extends VBox {

    public CommandBlockPane() {
        this.setStyle("-fx-border-color: gray; -fx-padding: 10; -fx-spacing: 10;");
        this.getChildren().add(new Label("🔧 Drag commands here"));

        this.setOnDragOver(event -> {
            if (event.getGestureSource() != this && event.getDragboard().hasString()) {
                event.acceptTransferModes(TransferMode.COPY_OR_MOVE);
            }
            event.consume();
        });

        this.setOnDragDropped(event -> {
            Dragboard db = event.getDragboard();
            boolean success = false;
            if (db.hasString()) {
                String command = db.getString();
                Label cmdLabel = new Label("➤ " + command);
                this.getChildren().add(cmdLabel);
                success = true;
            }
            event.setDropCompleted(success);
            event.consume();
        });
    }
}
