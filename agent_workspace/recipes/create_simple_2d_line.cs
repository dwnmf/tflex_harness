using System;
using System.IO;
using TFlex;
using TFlex.Model;
using TFlex.Model.Model2D;

public class Program
{
    public static int Main()
    {
        string fileName = Environment.GetEnvironmentVariable("TFLEX_RECIPE_OUTPUT_FILE");
        if (String.IsNullOrWhiteSpace(fileName))
        {
            Console.Error.WriteLine("TFLEX_RECIPE_OUTPUT_FILE is required");
            return 2;
        }

        Directory.CreateDirectory(Path.GetDirectoryName(fileName));

        var setup = new ApplicationSessionSetup();
        setup.ReadOnly = false;
        setup.Enable3D = false;
        setup.EnableDOCs = false;
        setup.EnableMacros = false;
        setup.PromptToSaveModifiedDocuments = false;
        setup.ProtectionLicense = ApplicationSessionSetup.License.TFlexAPI;

        bool init = Application.InitSession(setup);
        Console.WriteLine("init=" + init);
        if (!init) return 10;

        Document doc = null;
        try
        {
            doc = Application.NewDocument(false, false);
            Console.WriteLine("docNull=" + (doc == null));
            if (doc == null) return 11;

            doc.BeginChanges("simple 2d line");
            FreeNode n1 = new FreeNode(doc, 10, 10);
            FreeNode n2 = new FreeNode(doc, 50, 10);
            LineConstruction line = new LineConstruction(doc);
            line.SetThroughNodes(n1, n2);
            var endResult = doc.EndChanges();

            Console.WriteLine("endChanges=" + endResult);
            Console.WriteLine("n1=" + n1.X.Value + "," + n1.Y.Value);
            Console.WriteLine("n2=" + n2.X.Value + "," + n2.Y.Value);
            Console.WriteLine("lineType=" + line.LineType);
            int object2DCount = 0;
            foreach (Object2D obj in doc.Get2DObjects())
            {
                object2DCount++;
                Console.WriteLine("object2dType=" + obj.GetType().FullName);
            }
            Console.WriteLine("objects2d=" + object2DCount);

            bool saved = doc.SaveAs(fileName);
            Console.WriteLine("saved=" + saved);
            Console.WriteLine("exists=" + File.Exists(fileName));
            Console.WriteLine("fileName=" + doc.FileName);
            doc.Close();
            doc = null;
            return saved && File.Exists(fileName) && endResult.ToString() == "OK" && object2DCount >= 3 ? 0 : 12;
        }
        finally
        {
            if (doc != null) doc.Close();
            if (Application.IsSessionInitialized) Application.ExitSession();
            Console.WriteLine("session=" + Application.IsSessionInitialized);
        }
    }
}
