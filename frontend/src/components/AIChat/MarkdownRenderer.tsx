"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="markdown-body text-sm leading-relaxed max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
        components={{
          code: ({ inline, children, ...props }: any) => {
            if (inline) {
              return (
                <code className="bg-[var(--bg-surface)] px-1 rounded text-sm font-mono" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <pre className="rounded-md bg-[#0f172a] text-white p-3 overflow-auto">
                <code {...props}>{children}</code>
              </pre>
            );
          },
          a: ({ href, children, ...props }: any) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--peach)] underline" {...props}>
              {children}
            </a>
          ),
          table: ({ children }: any) => (
            <div className="overflow-auto">
              <table className="w-full text-sm table-auto border-collapse">{children}</table>
            </div>
          ),
          th: ({ children }: any) => <th className="px-2 py-1 border-b text-left font-semibold">{children}</th>,
          td: ({ children }: any) => <td className="px-2 py-1 border-b align-top">{children}</td>,
          ul: ({ children }: any) => <ul className="list-disc pl-5">{children}</ul>,
          ol: ({ children }: any) => <ol className="list-decimal pl-5">{children}</ol>,
        }}
      >
        {content ?? ""}
      </ReactMarkdown>
    </div>
  );
}
