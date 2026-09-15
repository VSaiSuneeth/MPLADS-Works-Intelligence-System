import { test, expect } from '@playwright/test';

test.describe('Digital Memory Vault End-to-End Tests', () => {
  test('should display Navbar and navigate between tabs', async ({ page }) => {
    await page.goto('/');

    // Check title and logo
    await expect(page).toHaveTitle(/Digital Memory Vault/);
    await expect(page.getByText('MemoryVault')).toBeVisible();

    // Verify tabs exist
    await expect(page.getByRole('button', { name: 'Timeline' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Semantic Search' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Events & Stories' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Duplicate Review' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'On This Day' })).toBeVisible();

    // Navigate to Search tab
    await page.getByRole('button', { name: 'Semantic Search' }).click();
    await expect(page.getByRole('heading', { name: /Find Anything in Your Life Vault/i })).toBeVisible();

    // Navigate to Events tab
    await page.getByRole('button', { name: 'Events & Stories' }).click();
    await expect(page.getByRole('heading', { name: /Auto-Clustered Events/i })).toBeVisible();

    // Navigate to Duplicates tab
    await page.getByRole('button', { name: 'Duplicate Review' }).click();
    await expect(page.getByRole('heading', { name: /Duplicate Review Center/i })).toBeVisible();

    // Navigate to Flashbacks tab
    await page.getByRole('button', { name: 'On This Day' }).click();
    await expect(page.getByRole('heading', { name: /On This Day & Life Highlights/i })).toBeVisible();
  });

  test('should open Add Memory modal and allow creating note', async ({ page }) => {
    await page.goto('/');

    // Click Add Memory
    await page.locator('#add-memory-btn').click();
    await expect(page.getByRole('heading', { name: 'Add Memory to Vault' })).toBeVisible();

    // Switch to Write Note tab
    await page.getByRole('button', { name: 'Write Note' }).click();
    await page.getByPlaceholder('e.g. Reflections on Goa Trip').fill('E2E Test Note');
    await page.getByPlaceholder('Write your memory or thought here...').fill('Playwright automated e2e verification note.');
    
    // Save note
    await page.getByRole('button', { name: 'Save Note to Vault' }).click();

    // Verify modal closes
    await expect(page.getByRole('heading', { name: 'Add Memory to Vault' })).not.toBeVisible();
  });

  test('should execute semantic natural language search', async ({ page }) => {
    await page.goto('/');

    // Go to search
    await page.getByRole('button', { name: 'Semantic Search' }).click();
    
    // Enter query
    const searchInput = page.locator('#search-input');
    await searchInput.fill('Goa beach sunset');
    await page.locator('#search-submit-btn').click();

    // Expect results
    await expect(page.getByRole('heading', { name: /Search Results/i })).toBeVisible();
  });
});
