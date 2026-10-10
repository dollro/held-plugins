import { expect, test } from '@playwright/test'

// Seeded by `manage.py seed_e2e_user` (task dev:seed-e2e, and in CI).
const email = process.env.E2E_USER_EMAIL ?? 'e2e@example.com'
const password = process.env.E2E_USER_PASSWORD ?? 'e2e-password-123'

test('log in, open the app and receive a live event', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('link', { name: 'Log in' }).click()
  // allauth's login page
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign In', exact: true }).click()

  await expect(page).toHaveURL(/\/app\//)
  await expect(page.getByTestId('current-user')).toHaveText(email)
  // Runtime config: rendered by Django, not compiled into the bundle.
  await expect(page.getByTestId('environment')).toHaveText('ci')
  // >>> realtime
  await expect(page.getByTestId('stream-status')).toHaveText('Event stream: connected')

  await page.getByTestId('send-test-event').click()
  await expect(page.getByTestId('events')).toContainText('Hello from Celery')
  // <<< realtime

  await page.getByRole('button', { name: 'Log out' }).click()
  await expect(page).toHaveURL(/\/$/)
})

test('the app sends anonymous users to the login page', async ({ page }) => {
  await page.goto('/app/')
  await expect(page).toHaveURL(/\/accounts\/login\/\?next=%2Fapp%2F$/)
})
