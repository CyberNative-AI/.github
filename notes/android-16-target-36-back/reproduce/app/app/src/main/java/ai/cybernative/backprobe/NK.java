package ai.cybernative.backprobe;
import android.view.KeyEvent;
public class NK extends android.app.Activity {
  @Override public boolean onKeyDown(int code, KeyEvent e) {
    if (code == KeyEvent.KEYCODE_BACK) { M.hit("NK", "onKeyDown"); return true; }
    return super.onKeyDown(code, e);
  }
}
