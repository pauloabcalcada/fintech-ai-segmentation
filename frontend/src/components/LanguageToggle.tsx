import { useTranslation } from "react-i18next";

export function LanguageToggle() {
  const { i18n } = useTranslation();

  function setLanguage(lng: string) {
    i18n.changeLanguage(lng);
    localStorage.setItem("language", lng);
  }

  return (
    <div className="flex items-center gap-1">
      <button
        data-testid="lang-en"
        onClick={() => setLanguage("en")}
        aria-label="Switch to English"
        className="rounded px-1.5 py-0.5 text-base leading-none transition-opacity hover:opacity-80"
        style={{ opacity: i18n.language === "en" ? 1 : 0.4 }}
      >
        🇺🇸
      </button>
      <button
        data-testid="lang-pt-BR"
        onClick={() => setLanguage("pt-BR")}
        aria-label="Switch to Portuguese"
        className="rounded px-1.5 py-0.5 text-base leading-none transition-opacity hover:opacity-80"
        style={{ opacity: i18n.language === "pt-BR" ? 1 : 0.4 }}
      >
        🇧🇷
      </button>
    </div>
  );
}
