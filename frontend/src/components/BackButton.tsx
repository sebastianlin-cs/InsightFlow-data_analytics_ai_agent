import { useNavigate } from "react-router-dom";

type Props = {
  fallbackTo: string;
  label?: string;
};

export function BackButton({ fallbackTo, label = "Back" }: Props) {
  const navigate = useNavigate();

  function handleBack() {
    if (window.history.length > 1) {
      navigate(-1);
      return;
    }
    navigate(fallbackTo);
  }

  return (
    <button
      onClick={handleBack}
      className="inline-flex items-center rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
    >
      <span className="mr-2" aria-hidden="true">
        ←
      </span>
      {label}
    </button>
  );
}
