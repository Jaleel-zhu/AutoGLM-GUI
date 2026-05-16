# Markdown Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add markdown rendering support to chat messages so tables, lists, and formatted content display properly instead of as plain text.

**Architecture:** Create a shared `MarkdownContent` component using react-markdown + remark-gfm, then integrate it into both ChatKitPanel (layered mode) and DevicePanel (classic mode) by replacing plain text rendering.

**Tech Stack:** React, TypeScript, react-markdown, remark-gfm, Tailwind CSS

---

## File Structure

**New Files:**
- `frontend/src/components/MarkdownContent.tsx` - Shared markdown rendering component

**Modified Files:**
- `frontend/package.json` - Add react-markdown and remark-gfm dependencies
- `frontend/src/components/ChatKitPanel.tsx` - Replace plain text with markdown rendering (2 locations)
- `frontend/src/components/DevicePanel.tsx` - Replace plain text with markdown rendering (2 locations)

---

## Task 1: Install Dependencies

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Add dependencies to package.json**

Navigate to frontend directory and add the dependencies:

```bash
cd frontend
pnpm add react-markdown@^9.0.1 remark-gfm@^4.0.0
```

Expected output: Dependencies installed successfully

- [ ] **Step 2: Verify installation**

Check that dependencies are in package.json:

```bash
grep -A 2 "react-markdown" package.json
```

Expected output:
```
"react-markdown": "^9.0.1",
"remark-gfm": "^4.0.0"
```

- [ ] **Step 3: Commit dependency changes**

```bash
git add package.json pnpm-lock.yaml
git commit -m "feat: add react-markdown and remark-gfm dependencies"
```

---

## Task 2: Create MarkdownContent Component

**Files:**
- Create: `frontend/src/components/MarkdownContent.tsx`

- [ ] **Step 1: Create the MarkdownContent component file**

Create `frontend/src/components/MarkdownContent.tsx` with the following content:

```tsx
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
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto">
              <table {...props} />
            </div>
          ),
          code: ({ node, inline, ...props }) =>
            inline ? (
              <code className="whitespace-nowrap" {...props} />
            ) : (
              <code className="whitespace-pre-wrap" {...props} />
            ),
        } as Components
      }
    >
      {content}
    </ReactMarkdown>
  );
}
```

- [ ] **Step 2: Verify TypeScript compilation**

Run type check to ensure no errors:

```bash
cd frontend
pnpm type-check
```

Expected: No TypeScript errors related to MarkdownContent.tsx

- [ ] **Step 3: Commit the new component**

```bash
git add src/components/MarkdownContent.tsx
git commit -m "feat: create MarkdownContent component for markdown rendering"
```

---

## Task 3: Integrate MarkdownContent into ChatKitPanel

**Files:**
- Modify: `frontend/src/components/ChatKitPanel.tsx:1-1148`

- [ ] **Step 1: Add import for MarkdownContent**

Add the import at the top of ChatKitPanel.tsx (after existing imports, around line 54):

```tsx
import { MarkdownContent } from './MarkdownContent';
```

- [ ] **Step 2: Replace user message rendering (line ~847)**

Find this code around line 847:

```tsx
<p className="whitespace-pre-wrap">
  {message.content}
</p>
```

Replace it with:

```tsx
<MarkdownContent content={message.content} />
```

- [ ] **Step 3: Replace assistant message rendering (line ~977)**

Find this code around line 977:

```tsx
<p className="whitespace-pre-wrap">
  {message.content}
</p>
```

Replace it with:

```tsx
<MarkdownContent content={message.content} />
```

- [ ] **Step 4: Verify TypeScript compilation**

```bash
cd frontend
pnpm type-check
```

Expected: No TypeScript errors

- [ ] **Step 5: Run frontend linter**

```bash
cd frontend
pnpm lint
```

Expected: No linting errors (or only pre-existing warnings)

- [ ] **Step 6: Commit ChatKitPanel changes**

```bash
git add src/components/ChatKitPanel.tsx
git commit -m "feat: integrate markdown rendering in ChatKitPanel"
```

---

## Task 4: Integrate MarkdownContent into DevicePanel

**Files:**
- Modify: `frontend/src/components/DevicePanel.tsx:1-1264`

- [ ] **Step 1: Add import for MarkdownContent**

Add the import at the top of DevicePanel.tsx (after existing imports, around line 46):

```tsx
import { MarkdownContent } from './MarkdownContent';
```

- [ ] **Step 2: Replace assistant message rendering (line ~996)**

Find this code around line 996:

```tsx
<p className="whitespace-pre-wrap">
  {message.content}
</p>
```

Replace it with:

```tsx
<MarkdownContent content={message.content} />
```

- [ ] **Step 3: Replace user message rendering (line ~1037)**

Find this code around line 1037:

```tsx
<p className="whitespace-pre-wrap">
  {message.content}
</p>
```

Replace it with:

```tsx
<MarkdownContent content={message.content} />
```

- [ ] **Step 4: Verify TypeScript compilation**

```bash
cd frontend
pnpm type-check
```

Expected: No TypeScript errors

- [ ] **Step 5: Run frontend linter**

```bash
cd frontend
pnpm lint
```

Expected: No linting errors (or only pre-existing warnings)

- [ ] **Step 6: Commit DevicePanel changes**

```bash
git add src/components/DevicePanel.tsx
git commit -m "feat: integrate markdown rendering in DevicePanel"
```

---

## Task 5: Build and Manual Testing

**Files:**
- None (testing only)

- [ ] **Step 1: Build the frontend**

```bash
cd frontend
pnpm build
```

Expected: Build completes successfully with no errors

- [ ] **Step 2: Start development servers**

Terminal 1 - Backend:
```bash
cd /home/wzp/code/gui/0511/AutoGLM-GUI
uv run autoglm-gui --base-url http://localhost:8080/v1 --reload
```

Terminal 2 - Frontend:
```bash
cd frontend
pnpm dev
```

Expected: Both servers start successfully

- [ ] **Step 3: Test markdown table rendering**

1. Open browser to http://localhost:3000
2. Connect to a device
3. Send query: "用表格分析北京景点"
4. Verify: Table renders with proper borders and formatting (not raw markdown)

- [ ] **Step 4: Test markdown lists**

1. Send query: "列出三个要点"
2. Verify: Bulleted list renders properly

- [ ] **Step 5: Test markdown headings**

1. Send query: "用markdown格式回复，包含标题、列表和表格"
2. Verify: Headings, lists, and tables all render correctly

- [ ] **Step 6: Test dark mode**

1. Toggle theme to dark mode
2. Verify: Markdown content is readable with proper contrast

- [ ] **Step 7: Test in both chat modes**

1. Test in classic mode (DevicePanel)
2. Switch to layered mode (ChatKitPanel)
3. Verify: Markdown renders correctly in both modes

- [ ] **Step 8: Test plain text messages**

1. Send query: "你好"
2. Verify: Plain text messages still display correctly without markdown

- [ ] **Step 9: Document testing results**

Create a simple test summary noting:
- ✅ Tables render correctly
- ✅ Lists render correctly
- ✅ Headings render correctly
- ✅ Dark mode works
- ✅ Both chat modes work
- ✅ Plain text still works

---

## Verification Checklist

After completing all tasks:

- [ ] All TypeScript compilation passes
- [ ] All linting passes
- [ ] Frontend builds successfully
- [ ] Markdown tables render properly
- [ ] Markdown lists render properly
- [ ] Markdown headings render properly
- [ ] Dark mode styling works
- [ ] Both classic and layered modes work
- [ ] Plain text messages still work
- [ ] No visual regressions in message bubbles
- [ ] All changes committed with clear messages

---

## Rollback Plan

If issues are found after deployment:

1. Revert commits in reverse order:
   ```bash
   git revert HEAD~3..HEAD
   ```

2. Remove dependencies:
   ```bash
   cd frontend
   pnpm remove react-markdown remark-gfm
   ```

3. Rebuild and redeploy:
   ```bash
   pnpm build
   ```
