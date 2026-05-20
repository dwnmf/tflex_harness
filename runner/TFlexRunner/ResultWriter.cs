using System;
using System.IO;
using System.Text;

namespace TFlexRunner
{
    internal static class ResultWriter
    {
        public static void WriteObjectStart() { Console.Write("{"); }
        public static void WriteObjectEnd() { Console.WriteLine("}"); }

        public static void WriteProperty(string name, string value, bool comma)
        {
            Console.Write("\"" + Escape(name) + "\":\"" + Escape(value) + "\"");
            if (comma) Console.Write(",");
        }

        public static void WriteProperty(string name, bool value, bool comma)
        {
            Console.Write("\"" + Escape(name) + "\":" + (value ? "true" : "false"));
            if (comma) Console.Write(",");
        }

        public static void WriteRawProperty(string name, string raw)
        {
            Console.Write("\"" + Escape(name) + "\":" + raw);
        }

        public static void WriteJsonPair(TextWriter writer, string name, string value, bool comma)
        {
            writer.Write("\"" + Escape(name) + "\":\"" + Escape(value) + "\"");
            if (comma) writer.Write(",");
        }

        public static void WriteJsonPair(TextWriter writer, string name, bool value, bool comma)
        {
            writer.Write("\"" + Escape(name) + "\":" + (value ? "true" : "false"));
            if (comma) writer.Write(",");
        }

        private static string Escape(string value)
        {
            if (value == null) return "";
            var sb = new StringBuilder(value.Length + 8);
            foreach (char c in value)
            {
                switch (c)
                {
                    case '\\': sb.Append("\\\\"); break;
                    case '"': sb.Append("\\\""); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 32) sb.Append("\\u" + ((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            return sb.ToString();
        }
    }
}
