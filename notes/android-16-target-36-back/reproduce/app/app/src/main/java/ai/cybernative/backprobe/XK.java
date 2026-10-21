package ai.cybernative.backprobe;
import android.view.KeyEvent;
public class XK extends androidx.appcompat.app.AppCompatActivity {
  @Override public boolean onKeyDown(int code, KeyEvent e) {
    if (code == KeyEvent.KEYCODE_BACK) { M.hit("XK", "onKeyDown"); return true; }
    return super.onKeyDown(code, e);
  }
}
