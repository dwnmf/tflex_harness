using System;
using System.IO;
using System.Reflection;

namespace TFlexRunner
{
    internal static class SnippetHost
    {
        public static string ProbeAssemblies()
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
