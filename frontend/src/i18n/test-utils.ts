import i18n, { type i18n as I18nInstance, type InitOptions } from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import ptBR from "./pt-BR.json";

export function createTestI18n(lng = "en"): I18nInstance {
  const instance = i18n.createInstance();
  const options: InitOptions = {
    lng,
    fallbackLng: "en",
    interpolation: { escapeValue: false },
    resources: {
      en: { translation: en },
      "pt-BR": { translation: ptBR },
    },
    initImmediate: false,
  };
  instance.use(initReactI18next).init(options);
  return instance;
}
