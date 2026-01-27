
import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Wand2 } from 'lucide-react';

interface FileContextModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (description: string) => void;
    initialDescription: string;
    filename: string;
    isAnalyzing?: boolean;
    onReAnalyze?: () => void;
    isSaving?: boolean;
}

export function FileContextModal({
    isOpen,
    onClose,
    onSave,
    initialDescription,
    filename,
    isAnalyzing = false,
    onReAnalyze,
    isSaving = false
}: FileContextModalProps) {
    // State initialized from props
    const [description, setDescription] = useState(initialDescription);
    
    // Sync local state when initialDescription prop changes (e.g., after Re-Analyze)
    useEffect(() => {
        setDescription(initialDescription);
    }, [initialDescription]);

    const handleSave = () => {
        onSave(description);
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <span className="truncate max-w-[400px]">File Context: {filename}</span>
                    </DialogTitle>
                    <DialogDescription>
                        Review and enrich the AI-generated context. This context helps the bot understand how to use this file.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="relative">
                        <Textarea 
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="File context/description..."
                            className="min-h-[200px] font-mono text-sm pr-10"
                        />
                         {/* Optional: Floating action inside textarea if needed, 
                             but here we put re-analyze in footer or header */}
                    </div>
                </div>

                <DialogFooter className="flex items-center justify-between sm:justify-between w-full">
                    {onReAnalyze && (
                        <Button 
                            type="button" 
                            variant="secondary" 
                            size="sm"
                            onClick={onReAnalyze}
                            disabled={isAnalyzing}
                            className="text-purple-600 bg-purple-50 hover:bg-purple-100 dark:bg-purple-900/20 dark:text-purple-300"
                        >
                            {isAnalyzing ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    <Wand2 className="mr-2 h-4 w-4" />
                                    Re-Analyze
                                </>
                            )}
                        </Button>
                    )}

                    <div className="flex gap-2">
                        <Button type="button" variant="outline" onClick={onClose}>
                            Cancel
                        </Button>
                        <Button 
                            type="button" 
                            onClick={handleSave}
                            disabled={isSaving}
                            className="bg-purple-600 hover:bg-purple-700 text-white"
                        >
                            {isSaving ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                'Save Changes'
                            )}
                        </Button>
                    </div>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
