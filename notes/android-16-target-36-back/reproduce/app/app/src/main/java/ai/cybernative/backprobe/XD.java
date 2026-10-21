package ai.cybernative.backprobe;
import android.os.Bundle;
import androidx.activity.OnBackPressedCallback;
public class XD extends androidx.appcompat.app.AppCompatActivity {
  @Override protected void onCreate(Bundle b) {
    super.onCreate(b);
    getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
      @Override public void handleOnBackPressed() { M.hit("XD", "OnBackPressedCallback"); }
    });
  }
}
