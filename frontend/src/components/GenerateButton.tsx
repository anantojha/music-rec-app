import { Waveform } from "@/components/Waveform";

interface GenerateButtonProps {
  onGenerate: () => void;
  isGenerating: boolean;
  disabled: boolean;
}

export function GenerateButton({ onGenerate, isGenerating, disabled }: GenerateButtonProps) {
  if (isGenerating) {
    return <Waveform label="Analyzing taste + ranking candidates…" />;
  }

  return (
    <button className="btn btn-primary" onClick={onGenerate} disabled={disabled}>
      Generate recommendations
    </button>
  );
}
