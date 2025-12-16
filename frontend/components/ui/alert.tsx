import * as React from "react";
import { AlertCircle, CheckCircle2, Info, TriangleAlert } from "lucide-react";

import { cn } from "@/lib/utils";

const icons = {
  info: Info,
  success: CheckCircle2,
  warning: TriangleAlert,
  destructive: AlertCircle
};

export type AlertVariant = keyof typeof icons;

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { variant?: AlertVariant }
>(({ className, variant = "info", ...props }, ref) => {
  const Icon = icons[variant] ?? Info;
  return (
    <div
      ref={ref}
      className={cn(
        "flex w-full gap-3 rounded-2xl border border-border bg-secondary/40 px-4 py-3 text-sm text-muted-foreground",
        className
      )}
      role="alert"
      {...props}
    >
      <Icon className="mt-0.5 h-5 w-5 text-primary" />
      <div className="space-y-1">{props.children}</div>
    </div>
  );
});
Alert.displayName = "Alert";

const AlertTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => <h5 ref={ref} className={cn("text-sm font-semibold", className)} {...props} />
);
AlertTitle.displayName = "AlertTitle";

const AlertDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={cn("text-sm leading-relaxed text-muted-foreground", className)} {...props} />
  )
);
AlertDescription.displayName = "AlertDescription";

export { Alert, AlertDescription, AlertTitle };
