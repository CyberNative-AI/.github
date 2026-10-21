package ai.cybernative.backprobe;
import android.app.Dialog;
import android.os.Bundle;
import android.widget.TextView;
public class ND extends android.app.Activity {
  @Override protected void onCreate(Bundle b) {
    super.onCreate(b);
    Dialog d = new Dialog(this) { @Override public void onBackPressed() { M.hit("ND", "Dialog.onBackPressed"); } };
    TextView t = new TextView(this); t.setText("dialog"); d.setContentView(t); d.show();
  }
}
