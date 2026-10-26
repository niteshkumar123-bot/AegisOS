import {test,expect} from '@playwright/test';
test('login screen renders accessible controls',async({page})=>{await page.goto('/');await expect(page.getByRole('heading',{name:/build with confidence/i})).toBeVisible();await expect(page.getByLabel('Email')).toBeVisible();await expect(page.getByLabel('Password')).toBeVisible();});
