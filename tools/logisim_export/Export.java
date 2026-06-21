// Headless exporter that renders every circuit in a .circ using Logisim-
// Evolution's OWN drawing code (the same path as File > Export Image), so the
// output is the authentic Logisim appearance. Usage:
//   java -cp <logisim.jar>:. Export <input.circ> <out_dir> <scale>
import com.cburch.logisim.circuit.Circuit;
import com.cburch.logisim.circuit.CircuitState;
import com.cburch.logisim.comp.ComponentDrawContext;
import com.cburch.logisim.data.Bounds;
import com.cburch.logisim.file.Loader;
import com.cburch.logisim.file.LogisimFile;
import com.cburch.logisim.proj.Project;

import javax.imageio.ImageIO;
import java.awt.Canvas;
import java.awt.Color;
import java.awt.Component;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.File;

public class Export {
  // Large margin so pin-label text (which Logisim draws beyond the circuit's
  // reported bounds) is never clipped; build.py auto-crops to real content.
  static final int BORDER = 160;

  public static void main(String[] args) throws Exception {
    final File in = new File(args[0]);
    final File outDir = new File(args[1]);
    final double scale = args.length > 2 ? Double.parseDouble(args[2]) : 3.0;
    outDir.mkdirs();

    final Component dummy = new Canvas();
    final Loader loader = new Loader(dummy);
    final LogisimFile lf = loader.openLogisimFile(in);
    final Project proj = new Project(lf);

    for (final Circuit circ : lf.getCircuits()) {
      final Bounds bds = circ.getBounds().expand(BORDER);
      final int w = (int) Math.ceil(bds.getWidth() * scale);
      final int h = (int) Math.ceil(bds.getHeight() * scale);
      if (w <= 0 || h <= 0) {
        System.out.println("skip (empty): " + circ.getName());
        continue;
      }
      final BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
      final Graphics2D g = img.createGraphics();
      g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
      g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
      g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);
      g.setColor(Color.WHITE);
      g.fillRect(0, 0, w, h);

      // Logisim canvas dot grid: light dots on the 10-unit lattice (device 1px)
      g.setColor(new Color(0xD8, 0xD8, 0xDE));
      final int gx0 = (int) (Math.floor(bds.getX() / 10.0) * 10);
      final int gy0 = (int) (Math.floor(bds.getY() / 10.0) * 10);
      final int gx1 = bds.getX() + bds.getWidth();
      final int gy1 = bds.getY() + bds.getHeight();
      for (int lx = gx0; lx <= gx1; lx += 10) {
        final int dx = (int) Math.round((lx - bds.getX()) * scale);
        for (int ly = gy0; ly <= gy1; ly += 10) {
          final int dy = (int) Math.round((ly - bds.getY()) * scale);
          g.fillRect(dx, dy, 1, 1);
        }
      }

      g.setColor(Color.BLACK);
      g.scale(scale, scale);
      g.translate(-bds.getX(), -bds.getY());

      final CircuitState cs = proj.getCircuitState(circ);
      final ComponentDrawContext ctx = new ComponentDrawContext(dummy, circ, cs, g, g);
      circ.draw(ctx, null);
      g.dispose();

      final File out = new File(outDir, circ.getName().replace(' ', '_') + ".png");
      ImageIO.write(img, "png", out);
      System.out.println("exported " + out.getName() + "  (" + w + "x" + h + ")");
    }
    System.out.println("DONE");
    System.exit(0);
  }
}
