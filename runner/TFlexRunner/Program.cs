using System;

namespace TFlexRunner
{
    internal static class Program
    {
        private static int Main(string[] args)
        {
            try
            {
                if (args.Length == 0 || args[0] == "env")
                {
                    ResultWriter.WriteObjectStart();
                    ResultWriter.WriteProperty("ok", true, comma: true);
                    ResultWriter.WriteProperty("runner", "TFlexRunner", comma: true);
                    ResultWriter.WriteProperty("framework", Environment.Version.ToString(), comma: true);
                    ResultWriter.WriteProperty("is64BitProcess", Environment.Is64BitProcess, comma: true);
                    ResultWriter.WriteProperty("baseDirectory", AppDomain.CurrentDomain.BaseDirectory, comma: true);
                    ResultWriter.WriteRawProperty("assemblies", SnippetHost.ProbeAssemblies());
                    ResultWriter.WriteObjectEnd();
                    return 0;
                }

                Console.Error.WriteLine("Unsupported command. Use: TFlexRunner.exe env");
                return 2;
            }
            catch (Exception ex)
            {
                ResultWriter.WriteObjectStart();
                ResultWriter.WriteProperty("ok", false, comma: true);
                ResultWriter.WriteProperty("exception", ex.ToString(), comma: false);
                ResultWriter.WriteObjectEnd();
                return 1;
            }
        }
    }
}
