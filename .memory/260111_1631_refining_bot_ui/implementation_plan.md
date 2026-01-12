## Goal Description
1. **Enable System Prompt Editing**: Allow users to edit the "Custom System Prompt" directly from the Bot Details page.
2. **Remove Specific Branding**: Remove "JVC" specific branding/hardcoding to prepare for a generic Freemium/Premium SaaS model.
3. **Global Design System Upgrade**: Apply the "MarkaJiap" design system (Thai Lucky Colors: Purple & Gold) globally.

## User Review Required
> [!NOTE]
> This change affects the Frontend only. Backend `PATCH /bots/{id}` already supports `system_prompt` updates.

## Proposed Changes

### Frontend (Admin Dashboard)

#### [MODIFY] [page.tsx](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/app/admin/bots/[id]/page.tsx)
- Add local state: `isEditingPrompt`, `promptValue`.
- Add `updateBotMutation` using `api.patch`.
- Update "Custom System Prompt" Card:
  - Add "Edit" button to Header.
  - When editing, replace `<pre>` view with `<Textarea>`.
  - Add "Save" and "Cancel" actions.

#### [MODIFY] [admin-sidebar.tsx](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/components/admin-sidebar.tsx)
- Change text "JVC AI Support Admin" to "AI Support Platform".
- Ensure logo usage is generic.

#### [MODIFY] [layout.tsx](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/app/layout.tsx)
- Update metadata title from "JVC AI Support Admin" to "AI Support Platform".

#### [MODIFY] [globals.css](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/app/globals.css)
- Implement CSS variables from `design_system.md` (Luck Purple, Success Gold, Dark Backgrounds).
- Set base body styles (Fonts, Background).

#### [MODIFY] [ui/*](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/components/ui/)
- Update `button.tsx`, `card.tsx` to use new CSS variables and styles (Glow effects, border colors).

## Verification Plan

### Manual Verification
1. Navigate to Bot Details page.
2. Click "Edit" on System Prompt card.
3. Change text and click "Save".
4. Verify toast success message and updated view.
5. Reload page to verify persistence.
