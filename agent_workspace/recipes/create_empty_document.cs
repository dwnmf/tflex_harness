using System;
using System.IO;
using TFlex;
using TFlex.Model;

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

            Console.WriteLine("title=" + doc.Title);
            bool saved = doc.SaveAs(fileName);
            Console.WriteLine("saved=" + saved);
            Console.WriteLine("exists=" + File.Exists(fileName));
            Console.WriteLine("fileName=" + doc.FileName);
            doc.Close();
            doc = null;
            return saved && File.Exists(fileName) ? 0 : 12;
        }
        finally
        {
            if (doc != null) doc.Close();
            if (Application.IsSessionInitialized) Application.ExitSession();
            Console.WriteLine("session=" + Application.IsSessionInitialized);
        }
    }
}
