import { Link } from 'react-router-dom';
import { Tool } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Star, ExternalLink, Pencil, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ToolCardProps {
  tool: Tool;
  showActions?: boolean;
  onEdit?: (tool: Tool) => void;
  onDelete?: (tool: Tool) => void;
}

export function ToolCard({ tool, showActions, onEdit, onDelete }: ToolCardProps) {
  const getCategoryVariant = (category: string) => {
    const variants: Record<string, 'development' | 'design' | 'productivity' | 'communication' | 'analytics' | 'other'> = {
      development: 'development',
      design: 'design',
      productivity: 'productivity',
      communication: 'communication',
      analytics: 'analytics',
      other: 'other',
    };
    return variants[category] || 'other';
  };

  const getStatusVariant = (status: string) => {
    const variants: Record<string, 'pending' | 'approved' | 'rejected'> = {
      pending: 'pending',
      approved: 'approved',
      rejected: 'rejected',
    };
    return variants[status] || 'pending';
  };

  return (
    <Card className="group overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-primary/5 hover:border-primary/20">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <Link to={`/tools/${tool.id}`} className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg truncate group-hover:text-primary transition-colors">
              {tool.name}
            </h3>
          </Link>
          <div className="flex gap-1.5 flex-shrink-0">
            <Badge variant={getCategoryVariant(tool.category)}>
              {tool.category}
            </Badge>
            <Badge variant={getStatusVariant(tool.status)}>
              {tool.status}
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pb-3">
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
          {tool.description}
        </p>
        
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <Star
                key={star}
                className={cn(
                  'h-4 w-4',
                  star <= Math.round(tool.average_rating)
                    ? 'fill-warning text-warning'
                    : 'text-muted-foreground/30'
                )}
              />
            ))}
          </div>
          <span className="text-sm text-muted-foreground">
           {tool.average_rating?.toFixed(1) || '0.0'} ({tool.total_ratings || 0})
          </span>
        </div>
      </CardContent>

      <CardFooter className="pt-3 border-t flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          by {tool.created_by}
        </span>
        
        <div className="flex items-center gap-2">
          {showActions && (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onEdit?.(tool)}
              >
                <Pencil className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={() => onDelete?.(tool)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </>
          )}
          <a href={tool.url} target="_blank" rel="noopener noreferrer">
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ExternalLink className="h-4 w-4" />
            </Button>
          </a>
        </div>
      </CardFooter>
    </Card>
  );
}
