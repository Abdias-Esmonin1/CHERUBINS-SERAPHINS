"use client";

import { Label } from "@/components/ui/label";
import { isTranslationOwnerView, type TranslationView } from "@/types/translation";
import type { LanguageBrief } from "@/types/catalog";

const TRANSLATION_TYPE_LABEL: Record<string, string> = {
  OFFICIAL: "Officielle",
  AUTHOR: "De l'auteur",
  HUMAN: "Traduction humaine",
  AI_GENERATED: "IA générée",
};

interface LanguageOption {
  code: string;
  name: string;
  content: string;
  translationType: string | null;
}

interface TranslationSelectorProps {
  originalLanguage: LanguageBrief;
  originalContent: string;
  translations: TranslationView[];
  selectedCode: string;
  onSelectCode: (code: string) => void;
  textSizeClassName: string;
}

/**
 * N'affiche que les traductions réellement consultables : celles dont
 * l'appelant est auteur/ADMIN (isTranslationOwnerView), ou disponibles
 * publiquement (available=true) — jamais une traduction non autorisée,
 * conformément à la règle de visibilité (Livrable 4 §5, écran 05).
 */
export function TranslationSelector({
  originalLanguage,
  originalContent,
  translations,
  selectedCode,
  onSelectCode,
  textSizeClassName,
}: TranslationSelectorProps) {
  const visibleTranslations = translations.filter(
    (translation) => isTranslationOwnerView(translation) || translation.available
  );

  const options: LanguageOption[] = [
    {
      code: originalLanguage.code,
      name: `${originalLanguage.name} (originale)`,
      content: originalContent,
      translationType: null,
    },
    ...visibleTranslations.map((translation) => ({
      code: translation.target_language.code,
      name: translation.target_language.name,
      content: translation.content ?? "",
      translationType: translation.translation_type,
    })),
  ];

  const selected = options.find((option) => option.code === selectedCode) ?? options[0];

  return (
    <div className="flex flex-col gap-3">
      {options.length > 1 && (
        <div className="flex flex-col gap-1.5 sm:w-64">
          <Label htmlFor="translation-language">Langue</Label>
          <select
            id="translation-language"
            value={selected.code}
            onChange={(event) => onSelectCode(event.target.value)}
            className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm"
          >
            {options.map((option) => (
              <option key={option.code} value={option.code}>
                {option.name}
              </option>
            ))}
          </select>
        </div>
      )}
      {selected.translationType && (
        <p className="text-sm text-muted-foreground">
          {TRANSLATION_TYPE_LABEL[selected.translationType] ?? selected.translationType}
        </p>
      )}
      <div className={`whitespace-pre-wrap leading-relaxed ${textSizeClassName}`}>{selected.content}</div>
    </div>
  );
}
