import { HomeIcon } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "../components/ui/button";
import { useNavigate } from "react-router-dom";

export function HomeButton() {
  useTheme();
  const navigate = useNavigate();
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => navigate("/")}
      className="h-9 w-9"
    >
      <HomeIcon className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <HomeIcon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Go home</span>
    </Button>
  );
}
