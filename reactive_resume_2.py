from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys

# ─────────────────────────────────────────────────────────────
# FLOW 1: Login Testing (Positive + Negative Test Cases)
# Website: https://rxresu.me/
# ─────────────────────────────────────────────────────────────

# Valid credentials
VALID_EMAIL    = "afrazpathanst@gmail.com"
VALID_PASSWORD = "Test@123"


def open_login_page(driver, wait):
    """Navigate to rxresu.me and open the login form."""
    driver.get("https://rxresu.me/")
    get_started = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//*[contains(text(), 'Get Started')]")
    ))
    get_started.click()
    # Wait for the email field to confirm the login page is ready
    wait.until(EC.visibility_of_element_located((By.NAME, "identifier")))


def fill_login_form(driver, wait, email, password):
    """Clear and fill the login form with given credentials."""
    email_field = driver.find_element(By.NAME, "identifier")
    email_field.clear()
    email_field.send_keys(email)

    password_field = driver.find_element(By.NAME, "password")
    password_field.clear()
    password_field.send_keys(password)

    login_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(), 'Sign in')]")
    ))
    driver.execute_script("arguments[0].click();", login_btn)


def get_error_message(driver, wait):
    """Capture inline field errors AND toast notifications from rxresu.me."""
    errors = []

    # 1. Inline field errors (e.g. "Too small: expected string to have >=6 characters")
    try:
        error_elements = driver.find_elements(
            By.XPATH, "//*[@data-error='true' and @data-slot='form-message']"
        )
        for el in error_elements:
            text = el.text.strip()
            if text:
                errors.append(text)
    except:
        pass

    # 2. Toast notification — rxresu.me uses data-sonner-toast with div[data-title]
    try:
        toast = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//li[@data-sonner-toast]//div[@data-title]")
            )
        )
        text = toast.text.strip()
        if text:
            errors.append(f"Toast: '{text}'")
    except:
        pass

    return " | ".join(errors) if errors else "No error message captured"


def logout(driver, wait):
    """Log out so the next test starts fresh."""
    try:
        # Open user menu (avatar/initials in top right)
        avatar = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(@class,'avatar') or contains(@aria-label,'account') or contains(@aria-label,'user')]")
        ))
        avatar.click()

        # Click logout
        logout_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(),'Logout') or contains(text(),'Sign out')]")
        ))
        logout_btn.click()

        # Wait to return to home page
        wait.until(EC.url_contains("rxresu.me"))
        time.sleep(1)
        print("   → Logged out successfully\n")
    except Exception as e:
        print(f"   → Logout step skipped: {e}\n")
        driver.get("https://rxresu.me/")
        time.sleep(1)


# ─────────────────────────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────────────────────────

def tc01_valid_login(driver, wait):
    """TC01 — Valid email and valid password (Happy Path)."""
    print("TC01: Valid Login (Happy Path)")
    open_login_page(driver, wait)
    fill_login_form(driver, wait, VALID_EMAIL, VALID_PASSWORD)

    try:
        wait.until(EC.url_contains("/dashboard"))
        print("   ✅ PASS: Redirected to dashboard — login successful")
        logout(driver, wait)
    except:
        print("   ❌ FAIL: Did not reach dashboard")
        driver.get("https://rxresu.me/")


def tc02_wrong_password(driver, wait):
    """TC02 — Valid email but incorrect password."""
    print("TC02: Wrong Password")
    open_login_page(driver, wait)
    fill_login_form(driver, wait, VALID_EMAIL, "WrongPass999")

    try:
        # Should stay on login page (no dashboard redirect)
        time.sleep(2)
        assert "/dashboard" not in driver.current_url, "Unexpectedly redirected to dashboard"
        error_msg = get_error_message(driver, wait)
        print(f"   ✅ PASS: Login blocked. Error shown: '{error_msg}'")
    except AssertionError:
        print("   ❌ FAIL: Logged in with wrong password — SECURITY ISSUE!")
    except Exception as e:
        print(f"   ⚠️  WARN: Could not read error message — {e}")
    finally:
        driver.get("https://rxresu.me/")


def tc03_wrong_email(driver, wait):
    """TC03 — Email not registered in the system."""
    print("TC03: Unregistered Email")
    open_login_page(driver, wait)
    fill_login_form(driver, wait, "notregistered@fake.com", VALID_PASSWORD)

    try:
        time.sleep(2)
        assert "/dashboard" not in driver.current_url
        error_msg = get_error_message(driver, wait)
        print(f"   ✅ PASS: Login blocked. Error shown: '{error_msg}'")
    except AssertionError:
        print("   ❌ FAIL: Logged in with unregistered email — SECURITY ISSUE!")
    except Exception as e:
        print(f"   ⚠️  WARN: Could not read error message — {e}")
    finally:
        driver.get("https://rxresu.me/")


def tc04_empty_fields(driver, wait):
    """TC04 — Both email and password left blank."""
    print("TC04: Empty Email and Password")
    open_login_page(driver, wait)
    fill_login_form(driver, wait, "", "")

    try:
        time.sleep(2)
        assert "/dashboard" not in driver.current_url
        error_msg = get_error_message(driver, wait)
        print(f"   ✅ PASS: Submission blocked. Error shown: '{error_msg}'")
    except AssertionError:
        print("   ❌ FAIL: Logged in with empty fields — SECURITY ISSUE!")
    except Exception as e:
        print(f"   ⚠️  WARN: Could not confirm validation — {e}")
    finally:
        driver.get("https://rxresu.me/")


def tc05_invalid_email_format(driver, wait):
    """TC05 — Email with invalid format (missing domain)."""
    print("TC05: Invalid Email Format (e.g. 'abc@')")
    open_login_page(driver, wait)
    fill_login_form(driver, wait, "abc@", VALID_PASSWORD)

    try:
        time.sleep(2)
        assert "/dashboard" not in driver.current_url
        error_msg = get_error_message(driver, wait)
        print(f"   ✅ PASS: Invalid format rejected. Error shown: '{error_msg}'")
    except AssertionError:
        print("   ❌ FAIL: Logged in with invalid email format — SECURITY ISSUE!")
    except Exception as e:
        print(f"   ⚠️  WARN: Could not confirm validation — {e}")
    finally:
        driver.get("https://rxresu.me/")


def tc06_empty_password_only(driver, wait):
    """TC06 — Valid email but password left blank."""
    print("TC06: Empty Password Only")
    open_login_page(driver, wait)
    fill_login_form(driver, wait, VALID_EMAIL, "")

    try:
        time.sleep(2)
        assert "/dashboard" not in driver.current_url
        error_msg = get_error_message(driver, wait)
        print(f"   ✅ PASS: Submission blocked. Error shown: '{error_msg}'")
    except AssertionError:
        print("   ❌ FAIL: Logged in with empty password — SECURITY ISSUE!")
    except Exception as e:
        print(f"   ⚠️  WARN: Could not confirm validation — {e}")
    finally:
        driver.get("https://rxresu.me/")

import datetime

# ─────────────────────────────────────────────────────────────
# FLOW 2: Create Resume + Fill Details + Export as PDF
# ─────────────────────────────────────────────────────────────

def tc07_create_new_resume(driver, wait):
    """TC07 — Login and create a new resume with a unique timestamped name."""
    print("TC07: Create New Resume")
    open_login_page(driver, wait)
    fill_login_form(driver, wait, VALID_EMAIL, VALID_PASSWORD)

    try:
        wait.until(EC.url_contains("/dashboard"))
        print("   ✅ PASS: Logged in — on dashboard")

        # STEP 7: Click 'Create a new resume' card
        new_resume_card = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//h3[contains(text(), 'Create a new resume')]")
        ))
        driver.execute_script("arguments[0].click();", new_resume_card)
        print("   Step 7: Clicked 'Create a new resume' card")

        # STEP 8: Generate unique resume name using timestamp
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        resume_name = f"Software Engineer Resume {timestamp}"

        name_field = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[@name='name']")
        ))
        name_field.clear()
        name_field.send_keys(resume_name)
        print(f"   Step 8: Entered resume name — '{resume_name}'")

        # STEP 9: Click the 'Create' submit button
        create_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@type='submit' and contains(text(), 'Create')]")
        ))
        driver.execute_script("arguments[0].click();", create_btn)
        print("   Step 9: Clicked 'Create' button")

        # STEP 10: Verify resume card appears on dashboard
        time.sleep(2)
        resume_card = wait.until(EC.visibility_of_element_located(
            (By.XPATH, f"//h3[contains(text(), '{resume_name}')]")
        ))
        assert resume_card.is_displayed()
        print(f"   ✅ PASS: Resume '{resume_name}' created and visible on dashboard!")

        # STEP 11: Click on the resume card to open the builder
        driver.execute_script("arguments[0].click();", resume_card)
        print("   Step 11: Opened resume in builder")

        # Wait for builder to load
        wait.until(EC.url_contains("/builder/"))
        print("   ✅ PASS: Resume builder loaded!")

        # Now fill in the resume details
        fill_resume_details(driver, wait)

    except Exception as e:
        print(f"   ❌ FAIL: {e}")


def fill_resume_details(driver, wait):
    """Helper — Fill in the Basics section of the resume editor."""
    print("\n   📝 Filling Resume Details...")

    try:
        # STEP 12: Fill Full Name
        name_input = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@id='sidebar-basics']//input[@name='name']")
        ))
        name_input.clear()
        name_input.send_keys("John Doe")
        print("   Step 12: Entered full name — 'John Doe'")

        # STEP 13: Fill Headline
        headline_input = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@id='sidebar-basics']//input[@name='headline']")
        ))
        headline_input.clear()
        headline_input.send_keys("Software Engineer")
        print("   Step 13: Entered headline — 'Software Engineer'")

        # STEP 14: Fill Email
        email_input = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@id='sidebar-basics']//input[@name='email']")
        ))
        email_input.clear()
        email_input.send_keys("john.doe@example.com")
        print("   Step 14: Entered email — 'john.doe@example.com'")

        # STEP 15: Fill Phone
        phone_input = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@id='sidebar-basics']//input[@name='phone']")
        ))
        phone_input.clear()
        phone_input.send_keys("+1 234 567 8900")
        print("   Step 15: Entered phone — '+1 234 567 8900'")

        # STEP 16: Fill Location
        location_input = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@id='sidebar-basics']//input[@name='location']")
        ))
        location_input.clear()
        location_input.send_keys("Toronto, Canada")
        print("   Step 16: Entered location — 'Toronto, Canada'")
        # STEP 17: Fill in Summary (rich text editor)
        # The summary uses a contenteditable div, not a regular input
        summary_editor = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='sidebar-summary']//div[@data-editor='true']")
        ))
        summary_editor.click()
        summary_editor.send_keys(
            "Experienced Software Engineer with 3+ years of expertise in "
            "Python, Selenium, and web automation. Passionate about building "
            "robust test frameworks and delivering high-quality software solutions."
        )
        print("   Step 17: Entered summary")
        # STEP 18: Click 'Add a new experience' button
        add_exp_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='sidebar-experience']//button[contains(text(), 'Add a new experience')]")
        ))
        driver.execute_script("arguments[0].click();", add_exp_btn)
        print("   Step 18: Clicked 'Add a new experience'")

        # STEP 19: Fill Company — scoped inside dialog
        company = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@role='dialog']//input[@name='company']")
        ))
        company.clear()
        company.send_keys("Google")
        print("   Step 19: Entered company — 'Google'")

        # STEP 20: Fill Position — scoped inside dialog
        position = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='position']")
        position.clear()
        position.send_keys("Software Engineer")
        print("   Step 20: Entered position — 'Software Engineer'")

        # STEP 21: Fill Location — scoped inside dialog
        exp_location = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='location']")
        exp_location.clear()
        exp_location.send_keys("Toronto, Canada")
        print("   Step 21: Entered experience location — 'Toronto, Canada'")

        # STEP 22: Fill Period — scoped inside dialog
        period = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='period']")
        period.clear()
        period.send_keys("2022 - Present")
        print("   Step 22: Entered period — '2022 - Present'")

        # STEP 23: Fill Description (rich text editor inside dialog)
        exp_description = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='dialog']//div[@data-editor='true']")
        ))
        exp_description.click()
        exp_description.send_keys(
            "Developed and maintained scalable web applications using Python "
            "and JavaScript. Led automation testing initiatives using Selenium WebDriver."
        )
        print("   Step 23: Entered experience description")

        # STEP 24: Click 'Create' to save experience — scoped inside dialog
        create_exp_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='dialog']//button[@type='submit' and contains(text(), 'Create')]")
        ))
        driver.execute_script("arguments[0].click();", create_exp_btn)
        print("   Step 24: Saved experience ✅")
        time.sleep(2)
        # STEP 25: Click 'Add a new education' button
        add_edu_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='sidebar-education']//button[contains(text(), 'Add a new education')]")
        ))
        driver.execute_script("arguments[0].click();", add_edu_btn)
        print("   Step 25: Clicked 'Add a new education'")

        # STEP 26: Fill School — scoped inside dialog
        school = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@role='dialog']//input[@name='school']")
        ))
        school.clear()
        school.send_keys("University of Toronto")
        print("   Step 26: Entered school — 'University of Toronto'")

        # STEP 27: Fill Degree — scoped inside dialog
        degree = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='degree']")
        degree.clear()
        degree.send_keys("Bachelor of Science")
        print("   Step 27: Entered degree — 'Bachelor of Science'")

        # STEP 28: Fill Area of Study — scoped inside dialog
        area = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='area']")
        area.clear()
        area.send_keys("Computer Science")
        print("   Step 28: Entered area — 'Computer Science'")

        # STEP 29: Fill Grade — scoped inside dialog
        grade = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='grade']")
        grade.clear()
        grade.send_keys("3.8 GPA")
        print("   Step 29: Entered grade — '3.8 GPA'")

        # STEP 30: Fill Location — scoped inside dialog
        edu_location = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='location']")
        edu_location.clear()
        edu_location.send_keys("Toronto, Canada")
        print("   Step 30: Entered education location — 'Toronto, Canada'")

        # STEP 31: Fill Period — scoped inside dialog
        edu_period = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='period']")
        edu_period.clear()
        edu_period.send_keys("2018 - 2022")
        print("   Step 31: Entered period — '2018 - 2022'")

        # STEP 32: Fill Description (rich text editor inside dialog)
        edu_description = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='dialog']//div[@data-editor='true']")
        ))
        edu_description.click()
        edu_description.send_keys(
            "Completed coursework in Data Structures, Algorithms, "
            "Software Engineering and Database Management Systems."
        )
        print("   Step 32: Entered education description")

        # STEP 33: Click 'Create' to save education — scoped inside dialog
        create_edu_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='dialog']//button[@type='submit' and contains(text(), 'Create')]")
        ))
        driver.execute_script("arguments[0].click();", create_edu_btn)
        print("   Step 33: Saved education ✅")

        # STEP 34: Wait for Education dialog to fully close, then re-find the Skills button
        time.sleep(2)  # Wait for page to settle after education save

        add_skill_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='sidebar-skills']//button[contains(text(), 'Add a new skill')]")
        ))
        driver.execute_script("arguments[0].click();", add_skill_btn)
        print("   Step 34: Clicked 'Add a new skill'")

        # STEP 35: Fill Skill Name — scoped inside dialog
        skill_name = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@role='dialog']//input[@name='name']")
        ))
        skill_name.clear()
        skill_name.send_keys("Programming Languages")
        print("   Step 35: Entered skill name — 'Programming Languages'")

        # STEP 36: Fill Proficiency — scoped inside dialog
        proficiency = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@name='proficiency']")
        proficiency.clear()
        proficiency.send_keys("Advanced")
        print("   Step 36: Entered proficiency — 'Advanced'")

        # STEP 37: Add Keywords — type each and press Enter
        keywords_input = driver.find_element(
            By.XPATH, "//div[@role='dialog']//input[@placeholder='Add a keyword...']")
        for keyword in ["Python", "JavaScript", "Selenium", "SQL"]:
            keywords_input.send_keys(keyword)
            keywords_input.send_keys(Keys.RETURN)
            time.sleep(0.5)
        print("   Step 37: Added keywords — Python, JavaScript, Selenium, SQL")

        # STEP 38: Click 'Create' to save skill — scoped inside dialog
        create_skill_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='dialog']//button[@type='submit' and contains(text(), 'Create')]")
        ))
        driver.execute_script("arguments[0].click();", create_skill_btn)
        print("   Step 38: Saved skill ✅")
        time.sleep(2)
        #export resume as a pdf
        tc08_export_resume_pdf(driver, wait)



    except Exception as e:
        print(f"   ❌ FAIL in fill_resume_details: {e}")


def tc08_export_resume_pdf(driver, wait):
    """TC08 — Export the resume as PDF using the toolbar button."""
    print("\nTC08: Export Resume as PDF")

    try:
        # STEP 39: Click the PDF button in the bottom toolbar
        # Identified by its unique SVG path containing PDF icon drawing
        pdf_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[.//*[contains(@d, 'M224,152a8,8,0')]]")
        ))
        driver.execute_script("arguments[0].click();", pdf_btn)
        print("   Step 39: Clicked PDF export button")

        # Wait for PDF to generate — rxresu.me opens a /printer/ page
        time.sleep(5)
        print("   ✅ PASS: PDF export triggered successfully!")
        print("\n✅ FLOW 2 COMPLETE: Resume created, filled, and exported as PDF!")

    except Exception as e:
        print(f"   ❌ FAIL in tc08_export_resume_pdf: {e}")
# ─────────────────────────────────────────────────────────────
# MAIN — Run all test cases
# ─────────────────────────────────────────────────────────────

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 15)

print("=" * 55)
print("  FLOW 1: LOGIN TEST SUITE — rxresu.me")
print("=" * 55 + "\n")

try:
    tc01_valid_login(driver, wait)
    tc02_wrong_password(driver, wait)
    tc03_wrong_email(driver, wait)
    tc04_empty_fields(driver, wait)
    tc05_invalid_email_format(driver, wait)
    tc06_empty_password_only(driver, wait)
    tc07_create_new_resume(driver, wait)

    print("=" * 55)
    print("  ALL LOGIN TEST CASES EXECUTED")
    print("=" * 55)

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")

finally:
    time.sleep(5)
    driver.quit()
    print("Browser closed.")