import { test, expect } from '@playwright/test';

test.describe('DEI Extractor Basic Flow', () => {
  test('should load the homepage', async ({ page }) => {
    await page.goto('/');

    // Check if the main elements are present
    await expect(page.getByText('DEI Extractor')).toBeVisible();
    await expect(page.getByText('Extract data from bills')).toBeVisible();
  });

  test('should toggle language', async ({ page }) => {
    await page.goto('/');

    // Click language toggle
    await page.getByRole('button', { name: /toggle language/i }).click();

    // Check if language changed (this would need to be updated based on actual implementation)
    await expect(page.getByText('Upload Files')).toBeVisible();
  });

  test('should show upload zone', async ({ page }) => {
    await page.goto('/');

    // Check upload zone elements
    await expect(page.getByText('Ανέβασμα Αρχείων')).toBeVisible();
    await expect(page.getByText('Σύρετε και αφήστε τα PDF ή ZIP αρχεία σας εδώ')).toBeVisible();
  });

  test('should show options form', async ({ page }) => {
    await page.goto('/');

    // Check options form elements
    await expect(page.getByText('Επιλογές')).toBeVisible();
    await expect(page.getByText('Εκαθαριστικός Φιλτράρισμα')).toBeVisible();
    await expect(page.getByText('Λεπτομερή Αρχεία')).toBeVisible();
  });

  test('should show process panel', async ({ page }) => {
    await page.goto('/');

    // Check process panel elements
    await expect(page.getByText('Επεξεργασία')).toBeVisible();
    await expect(page.getByRole('button', { name: /Επεξεργασία Αρχείων/i })).toBeVisible();
  });

  test('should show history section', async ({ page }) => {
    await page.goto('/');

    // Check history section
    await expect(page.getByText('Ιστορικό')).toBeVisible();
    await expect(page.getByText('Δεν υπάρχει ιστορικό')).toBeVisible();
  });

  test('should show privacy note in footer', async ({ page }) => {
    await page.goto('/');

    // Check footer privacy note
    await expect(page.getByText(/Τα αρχεία επεξεργάζονται μόνο για την εξαγωγή δεδομένων/)).toBeVisible();
  });
});
