import i18n from "i18next";
import { initReactI18next } from "react-i18next";

i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: {
        "dev.tokens.title": "Design tokens",
        "login.title": "Sign in",
        "login.student": "Student",
        "login.staff": "Staff",
        "login.student_id": "Student ID",
        "login.email": "Email",
        "login.password": "Password",
        "login.submit": "Sign in",
        "login.invalid": "Invalid credentials",
        "login.forbidden": "This login is for instructors and TAs only",
        "login.section": "Choose a section"
      }
    }
  },
  lng: "en",
  fallbackLng: "en",
  interpolation: {
    escapeValue: false
  }
});

export default i18n;
