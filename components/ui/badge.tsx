import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium tracking-tight",
  {
    variants: {
      variant: {
        default: "border-border/60 bg-muted text-foreground",
        cyan: "border-cyan-400/25 bg-cyan-500/10 text-cyan-200",
        orange: "border-orange-400/25 bg-orange-500/10 text-orange-200",
        red: "border-red-400/25 bg-red-500/10 text-red-200",
        green: "border-emerald-400/25 bg-emerald-500/10 text-emerald-200",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }

