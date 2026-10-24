package ai.cybernative.winprobe;
import android.app.Activity; import android.content.res.Configuration; import android.graphics.Rect;
import android.os.Bundle; import android.util.Log; import android.view.Gravity; import android.view.WindowInsets;
import android.widget.FrameLayout; import android.widget.TextView;
public abstract class Base extends Activity {
  static int creates = 0;
  TextView tv;
  String arm() { return getClass().getSimpleName(); }
  void setup() {}
  boolean padInsets() { return false; }
  @Override protected void onCreate(Bundle b) {
    super.onCreate(b); creates++; setup();
    FrameLayout root = new FrameLayout(this);
    tv = new TextView(this); tv.setText("WINPROBE " + arm()); tv.setTextSize(28); tv.setBackgroundColor(0xFFFF8800);
    root.addView(tv, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.TOP));
    if (padInsets()) root.setOnApplyWindowInsetsListener((v, in) -> {
      android.graphics.Insets s = in.getInsets(WindowInsets.Type.systemBars());
      v.setPadding(s.left, s.top, s.right, s.bottom); return in; });
    setContentView(root);
  }
  @Override protected void onResume() { super.onResume(); tv.postDelayed(this::report, 800); }
  @Override public void onConfigurationChanged(Configuration c) { super.onConfigurationChanged(c); tv.postDelayed(this::report, 800); }
  void report() {
    int[] loc = new int[2]; tv.getLocationOnScreen(loc);
    WindowInsets wi = tv.getRootWindowInsets();
    int inset = wi == null ? -1 : wi.getInsets(WindowInsets.Type.statusBars()).top;
    int sbH = -1; int id = getResources().getIdentifier("status_bar_height", "dimen", "android"); if (id > 0) sbH = getResources().getDimensionPixelSize(id);
    Configuration c = getResources().getConfiguration();
    Rect wb = getWindowManager().getCurrentWindowMetrics().getBounds();
    Rect mb = getWindowManager().getMaximumWindowMetrics().getBounds();
    Log.i("WINPROBE", "R arm=" + arm() + " ori=" + (c.orientation == Configuration.ORIENTATION_LANDSCAPE ? "L" : c.orientation == Configuration.ORIENTATION_PORTRAIT ? "P" : "U")
      + " sw=" + c.smallestScreenWidthDp + " wdp=" + c.screenWidthDp + " hdp=" + c.screenHeightDp
      + " top=" + loc[1] + " inset=" + inset + " sbh=" + sbH + " win=" + wb.width() + "x" + wb.height() + " max=" + mb.width() + "x" + mb.height()
      + " req=" + getRequestedOrientation() + " creates=" + creates + " target=" + getApplicationInfo().targetSdkVersion);
  }
}
