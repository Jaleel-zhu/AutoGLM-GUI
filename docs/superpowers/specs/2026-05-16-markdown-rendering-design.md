# Markdown Rendering for Model Responses

**Date**: 2026-05-16  
**Issue**: https://github.com/suyiiyii/AutoGLM-GUI/issues/361  
**Status**: Approved

## Problem Statement

Currently, when AI models return markdown-formatted content (tables, lists, headings, etc.), the frontend displays it as plain text. This makes structured responses like tables unreadable.

**Example**: When asking "用表格分析北京景点", the model returns a markdown table, but users see raw markdown syntax instead of a formatted table.

## Goals

1. Render markdown content properly in all chat message areas
2. Support GitHub Flavored Markdown (tables, lists, headings, code blocks, links)
3. Maintain existing UI styling (message bubbles, colors, timestamps)
4. Support light/dark theme switching
5. Work in both classic and layered chat modes

## Non-Goals

- Syntax highlighting for code blocks (future enhancement)
- Custom markdown extensions (future enhancement)
- Editing markdown content
- Markdown input assistance

## Technical Design

### Architecture

**Component Structure**:
```
MarkdownContent (new shared component)
  ├─ react-markdown (rendering engine)
  ├─ remark-gfm (GFM plugin)
  └─ Tailwind typography (styling)

Used by:
  ├─ ChatKitPanel.tsx (layered mode)
  └─ DevicePanel.tsx (classic mode)
```

### Dependencies

Add to `frontend/package.json`:
```json
{
  "dependencies": {
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  }
}
```

**Why react-markdown?**
- Most popular React markdown library (13k+ stars)
- Secure by default (no `dangerouslySetInnerHTML`)
- Extensible plugin system
- Small bundle size (~50KB)
- Active maintenance

**Why remark-gfm?**
- Adds GitHub Flavored Markdown support
- Enables tables, strikethrough, task lists
- Official remark plugin

### Implementation

#### 1. Shared Component

**File**: `frontend/src/components/MarkdownContent.tsx`

```tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className={`prose prose-sm dark:prose-invert max-w-none ${className}`}
      components={{
        // Ensure tables are responsive
        table: ({ node, ...props }) => (
          <div className="overflow-x-auto">
            <table {...props} />
          </div>
        ),
        // Preserve whitespace in code blocks
        code: ({ node, inline, ...props }) => (
          inline ? (
            <code className="whitespace-nowrap" {...props} />
          ) : (
            <code className="whitespace-pre-wrap" {...props} />
          )
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
```

**Design decisions**:
- `prose-sm`: Smaller font size to match existing chat UI
- `max-w-none`: Allow full width within message bubbles
- `dark:prose-invert`: Automatic dark mode support
- Table wrapper: Horizontal scroll for wide tables
- Code handling: Inline vs block code whitespace

#### 2. Integration Points

**ChatKitPanel.tsx**:

Location 1 - User messages (line ~847):
```tsx
// Before:
<p className="whitespace-pre-wrap">{message.content}</p>

// After:
<MarkdownContent content={message.content} />
```

Location 2 - Assistant messages (line ~977):
```tsx
// Before:
<p className="whitespace-pre-wrap">{message.content}</p>

// After:
<MarkdownContent content={message.content} />
```

**DevicePanel.tsx**:

Location 1 - Assistant messages (line ~996):
```tsx
// Before:
<p className="whitespace-pre-wrap">{message.content}</p>

// After:
<MarkdownContent content={message.content} />
```

Location 2 - User messages (line ~1037):
```tsx
// Before:
<p className="whitespace-pre-wrap">{message.content}</p>

// After:
<MarkdownContent content={message.content} />
```

#### 3. Styling

**Tailwind Typography Configuration**:

The project already has `@tailwindcss/postcss` installed. The `prose` classes provide:
- Consistent typography (headings, paragraphs, lists)
- Table styling (borders, padding, striping)
- Code block styling (background, padding)
- Link styling (color, underline)
- Automatic dark mode with `dark:prose-invert`

**Custom Overrides** (if needed):
```css
/* In global CSS if default prose styles conflict */
.prose table {
  @apply border-collapse border border-slate-300 dark:border-slate-700;
}

.prose th,
.prose td {
  @apply border border-slate-300 dark:border-slate-700 px-3 py-2;
}
```

### Security

**XSS Protection**:
- react-markdown sanitizes HTML by default
- Does not render raw HTML unless explicitly enabled
- No use of `dangerouslySetInnerHTML`
- remark-gfm is a trusted plugin

**Content Validation**:
- No additional validation needed
- Model responses are already trusted content
- Markdown syntax errors gracefully degrade to plain text

### Performance

**Bundle Size Impact**:
- react-markdown: ~40KB gzipped
- remark-gfm: ~10KB gzipped
- Total: ~50KB additional bundle size

**Runtime Performance**:
- Markdown parsing is fast (<1ms for typical messages)
- React component rendering is efficient
- No performance impact on message streaming

### Compatibility

**Browser Support**:
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Same as existing React app requirements
- No special polyfills needed

**Existing Features**:
- ✅ Message streaming (works with partial markdown)
- ✅ Message history (markdown persisted as-is)
- ✅ Copy/paste (markdown source preserved)
- ✅ Internationalization (no text changes)

## Testing Plan

### Manual Testing

1. **Basic Markdown**:
   - Query: "列出三个要点"
   - Expected: Bulleted list renders properly

2. **Tables**:
   - Query: "用表格分析北京景点"
   - Expected: Table with borders and proper formatting

3. **Mixed Content**:
   - Query: "用markdown格式回复，包含标题、列表和表格"
   - Expected: All elements render correctly

4. **Theme Switching**:
   - Toggle light/dark mode
   - Expected: Markdown content adapts to theme

5. **Both Chat Modes**:
   - Test in classic mode (DevicePanel)
   - Test in layered mode (ChatKitPanel)
   - Expected: Consistent rendering in both

6. **Edge Cases**:
   - Empty content
   - Plain text (no markdown)
   - Malformed markdown
   - Very long tables
   - Code blocks with special characters

### Verification Checklist

- [ ] Tables render with borders and proper alignment
- [ ] Lists (ordered/unordered) display correctly
- [ ] Headings have appropriate sizing
- [ ] Code blocks preserve formatting
- [ ] Links are clickable and styled
- [ ] Dark mode styling works
- [ ] Message bubbles maintain existing styling
- [ ] Timestamps and status icons still visible
- [ ] No layout breaks with long content
- [ ] Horizontal scroll works for wide tables

## Rollout Plan

1. **Phase 1**: Add dependencies
   - Run `pnpm install` in frontend directory
   - Verify no conflicts

2. **Phase 2**: Create MarkdownContent component
   - Implement shared component
   - Test in isolation

3. **Phase 3**: Integrate into ChatKitPanel
   - Replace 2 locations
   - Test layered mode

4. **Phase 4**: Integrate into DevicePanel
   - Replace 2 locations
   - Test classic mode

5. **Phase 5**: Manual testing
   - Follow testing plan
   - Fix any styling issues

6. **Phase 6**: Commit and PR
   - Commit changes
   - Create pull request
   - Link to issue #361

## Future Enhancements

### Syntax Highlighting (Optional)
Add `rehype-highlight` or `rehype-prism` for code syntax highlighting:
```tsx
import rehypeHighlight from 'rehype-highlight';

<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  rehypePlugins={[rehypeHighlight]}
>
  {content}
</ReactMarkdown>
```

### Custom Components (Optional)
Override specific markdown elements:
```tsx
components={{
  a: ({ node, ...props }) => (
    <a {...props} target="_blank" rel="noopener noreferrer" />
  ),
  img: ({ node, ...props }) => (
    <img {...props} loading="lazy" />
  ),
}}
```

### Math Support (Optional)
Add `remark-math` + `rehype-katex` for LaTeX math rendering.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bundle size increase | Low | 50KB is acceptable for the feature value |
| Breaking existing styling | Medium | Test thoroughly, use scoped prose classes |
| Performance with large messages | Low | Markdown parsing is fast, React handles efficiently |
| Security (XSS) | Low | react-markdown sanitizes by default |
| Compatibility issues | Low | Well-maintained library, wide browser support |

## Success Metrics

- Tables and structured content render properly
- No visual regressions in existing UI
- No performance degradation
- Positive user feedback on issue #361

## References

- Issue: https://github.com/suyiiyii/AutoGLM-GUI/issues/361
- react-markdown: https://github.com/remarkjs/react-markdown
- remark-gfm: https://github.com/remarkjs/remark-gfm
- Tailwind Typography: https://tailwindcss.com/docs/typography-plugin
