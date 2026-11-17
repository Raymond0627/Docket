import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMarkdownProps {
  content: string;
}

/**
 * Renders Gemini's markdown replies (bold, lists, headers, tables, code)
 * styled to match the chat bubble look.
 */
export const ChatMarkdown: React.FC<ChatMarkdownProps> = ({ content }) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      p: ({ children }) => <p className="mb-1.5 last:mb-0">{children}</p>,
      strong: ({ children }) => (
        <strong className="font-bold text-slate-900 dark:text-white">{children}</strong>
      ),
      em: ({ children }) => <em className="italic">{children}</em>,
      ul: ({ children }) => (
        <ul className="mb-1.5 list-disc space-y-0.5 pl-4 last:mb-0">{children}</ul>
      ),
      ol: ({ children }) => (
        <ol className="mb-1.5 list-decimal space-y-0.5 pl-4 last:mb-0">{children}</ol>
      ),
      li: ({ children }) => <li className="marker:text-indigo-400">{children}</li>,
      h1: ({ children }) => (
        <h3 className="mb-1.5 text-xs font-bold text-slate-900 dark:text-white last:mb-0">{children}</h3>
      ),
      h2: ({ children }) => (
        <h3 className="mb-1.5 text-xs font-bold text-slate-900 dark:text-white last:mb-0">{children}</h3>
      ),
      h3: ({ children }) => (
        <h4 className="mb-1.5 text-xs font-bold text-slate-900 dark:text-white last:mb-0">{children}</h4>
      ),
      a: ({ children, href }) => (
        <a
          href={href}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-indigo-500 underline underline-offset-2"
        >
          {children}
        </a>
      ),
      code: ({ children, className }) =>
        className ? (
          <code className="block font-mono text-[11px]">{children}</code>
        ) : (
          <code className="rounded bg-slate-200/80 px-1 py-0.5 font-mono text-[11px] dark:bg-slate-700/80">
            {children}
          </code>
        ),
      pre: ({ children }) => (
        <pre className="mb-1.5 overflow-x-auto rounded-lg bg-slate-200/60 p-2 last:mb-0 dark:bg-slate-950/70">
          {children}
        </pre>
      ),
      table: ({ children }) => (
        <div className="mb-1.5 overflow-x-auto last:mb-0">
          <table className="w-full border-collapse text-left">{children}</table>
        </div>
      ),
      th: ({ children }) => (
        <th className="border border-slate-300 bg-slate-200/60 px-2 py-1 text-[11px] font-bold dark:border-slate-700 dark:bg-slate-800/60">
          {children}
        </th>
      ),
      td: ({ children }) => (
        <td className="border border-slate-300 px-2 py-1 text-[11px] dark:border-slate-700">{children}</td>
      ),
      blockquote: ({ children }) => (
        <blockquote className="mb-1.5 border-l-2 border-indigo-400 pl-2 italic last:mb-0">
          {children}
        </blockquote>
      ),
      hr: () => <hr className="my-2 border-slate-300 dark:border-slate-700" />,
    }}
  >
    {content}
  </ReactMarkdown>
);

export default ChatMarkdown;
