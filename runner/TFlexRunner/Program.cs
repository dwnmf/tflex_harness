using System;
using System.IO;
using System.Reflection;

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
                    ResultWriter.WriteRawProperty("assemblies", ProbeAssemblies());
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

        private static string ProbeAssemblies()
        {
            string[] names = { "TFlexAPI", "TFlexAPI3D", "TFlexAPIData", "TFlexCommandAPI" };
            var writer = new StringWriter();
            writer.Write("[");
            for (int i = 0; i < names.Length; i++)
            {
                if (i > 0) writer.Write(",");
                writer.Write("{");
                ResultWriter.WriteJsonPair(writer, "name", names[i], comma: true);
                try
                {
                    var asm = Assembly.Load(names[i]);
                    ResultWriter.WriteJsonPair(writer, "loaded", true, comma: true);
                    ResultWriter.WriteJsonPair(writer, "fullName", asm.FullName, comma: false);
                }
                catch (Exception ex)
                {
                    ResultWriter.WriteJsonPair(writer, "loaded", false, comma: true);
                    ResultWriter.WriteJsonPair(writer, "error", ex.Message, comma: false);
                }
                writer.Write("}");
            }
            writer.Write("]");
            return writer.ToString();
        }
    }
}
