import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({
  content,
  className = '',
}: MarkdownContentProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className={`prose prose-sm dark:prose-invert max-w-none ${className}`}
      components={
        {
          table: ({ ...props }) => (
            <div className="overflow-x-auto">
              <table {...props} />
            </div>
          ),
          code: ({ ...props }) => {
            const isInline = !props.className?.includes('language-');
            return isInline ? (
              <code className="whitespace-nowrap" {...props} />
            ) : (
              <code className="whitespace-pre-wrap" {...props} />
            );
          },
        } as Components
      }
    >
      {content}
    </ReactMarkdown>
  );
}
