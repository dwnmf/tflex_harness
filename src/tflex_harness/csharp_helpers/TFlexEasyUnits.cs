using System.Globalization;

namespace TFlexEasy {
  public static class EasyUnits {
    public static double MmToModel(double mm) {
      return mm / 1000.0;
    }

    public static double ModelToMm(double model) {
      return model * 1000.0;
    }

    public static double DegToRad(double deg) {
      return deg * System.Math.PI / 180.0;
    }

    public static string F(double value) {
      return value.ToString("0.########", CultureInfo.InvariantCulture);
    }
  }
}
