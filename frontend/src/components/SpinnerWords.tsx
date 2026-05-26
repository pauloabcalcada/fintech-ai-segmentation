import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

export function SpinnerWords() {
  const { t } = useTranslation();
  const phrases = t("customers.loadingPhrases", { returnObjects: true }) as string[];

  const [phraseIdx, setPhraseIdx] = useState(
    () => Math.floor(Math.random() * phrases.length)
  );
  const [dotIdx, setDotIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setPhraseIdx((i) => (i + 1) % phrases.length);
    }, 700);
    return () => clearInterval(id);
  }, [phrases.length]);

  useEffect(() => {
    const id = setInterval(() => {
      setDotIdx((i) => (i + 1) % DOTS.length);
    }, 80);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      className="p-6 flex items-center justify-center min-h-[120px]"
      data-testid="customer-detail-inline-loading"
    >
      <span className="text-sm text-muted-foreground font-mono">
        {DOTS[dotIdx]} {phrases[phraseIdx]}
      </span>
    </div>
  );
}
