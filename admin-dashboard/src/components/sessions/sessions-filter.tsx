import { Button } from "@/components/ui/button";
import {
  SelectProvider,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Bot } from "@/lib/api";
import { RotateCcw } from "lucide-react";

interface SessionsFilterProps {
  bots: Bot[];
  selectedBotId: string | null;
  onSelectBot: (botId: string | null) => void;
  selectedStatus: string | null;
  onSelectStatus: (status: string | null) => void;
  isGrouped: boolean;
  onToggleGroup: (checked: boolean) => void;
  onReset: () => void;
}

export function SessionsFilter({
  bots,
  selectedBotId,
  onSelectBot,
  selectedStatus,
  onSelectStatus,
  isGrouped,
  onToggleGroup,
  onReset,
}: SessionsFilterProps) {
  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 rounded-lg border bg-card text-card-foreground shadow-sm animate-in fade-in-50">
      <div className="flex-1 flex flex-col md:flex-row gap-4">
        {/* Bot Filter */}
        <div className="flex flex-col gap-2 min-w-[200px]">
          <Label htmlFor="bot-filter" className="text-xs font-semibold text-muted-foreground">
            Filter by Bot
          </Label>
          <SelectProvider
            value={selectedBotId || "all"}
            onValueChange={(value) => onSelectBot(value === "all" ? null : value)}
          >
            <div className="relative">
              <SelectTrigger id="bot-filter" className="h-9">
                <SelectValue placeholder="All Bots" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Bots</SelectItem>
                {bots.map((bot) => (
                  <SelectItem key={bot.id} value={bot.id}>
                    {bot.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </div>
          </SelectProvider>
        </div>

        {/* Status Filter */}
        <div className="flex flex-col gap-2 min-w-[150px]">
          <Label htmlFor="status-filter" className="text-xs font-semibold text-muted-foreground">
            Status
          </Label>
          <SelectProvider
            value={selectedStatus || "all"}
            onValueChange={(value) => onSelectStatus(value === "all" ? null : value)}
          >
            <div className="relative">
              <SelectTrigger id="status-filter" className="h-9">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </div>
          </SelectProvider>
        </div>
      </div>

      <div className="flex items-end gap-4 border-l pl-4 md:ml-auto">
        {/* Reset Button */}
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={onReset}
          className="h-9 text-muted-foreground hover:text-primary"
          title="Reset Filters"
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          Reset
        </Button>

        {/* Grouping Toggle */}
        <div className="flex flex-col gap-2 items-center min-w-[100px]">
            <Label htmlFor="group-toggle" className="text-xs font-semibold text-muted-foreground">
              Group by Bot
            </Label>
            <div className="flex items-center gap-2 h-9">
                <Switch
                    id="group-toggle"
                    checked={isGrouped}
                    onCheckedChange={onToggleGroup}
                />
                <Label htmlFor="group-toggle" className="text-sm cursor-pointer">
                    {isGrouped ? "On" : "Off"}
                </Label>
            </div>
        </div>
      </div>
    </div>
  );
}
