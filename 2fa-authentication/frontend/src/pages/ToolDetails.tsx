import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, Tool, Comment } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { MainLayout } from '@/components/layout/MainLayout';
import { StarRating } from '@/components/StarRating';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import {
  ExternalLink,
  Calendar,
  User,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  Pencil,
  Trash2,
  ArrowLeft,
  MessageCircle,
  Star,
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

export default function ToolDetails() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { toast } = useToast();
  const [tool, setTool] = useState<Tool | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [totalComments, setTotalComments] = useState(0);
  const [userRating, setUserRating] = useState<number | null>(null);
  const [newComment, setNewComment] = useState('');
  const [editingComment, setEditingComment] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isRating, setIsRating] = useState(false);
  const [isCommenting, setIsCommenting] = useState(false);
  const [commentsPage, setCommentsPage] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      setIsLoading(true);
      try {
        const [toolData, commentsData, ratingData] = await Promise.all([
          api.getTool(parseInt(id)),
          api.getComments(parseInt(id), 0, 10),
          api.getUserRating(parseInt(id)).catch(() => ({ rating: null })),
        ]);
        setTool(toolData);
        setComments(commentsData.comments);
        setTotalComments(commentsData.total);
        setUserRating(ratingData.rating);
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to load tool details',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [id, toast]);

  const handleRate = async (rating: number) => {
    if (!id || isRating) return;
    setIsRating(true);
    try {
      const response = await api.rateTool(parseInt(id), rating);
      setUserRating(rating);
      setTool((prev) =>
        prev ? { ...prev, average_rating: response.average_rating } : prev
      );
      toast({ title: 'Rating submitted', description: `You rated this tool ${rating} stars.` });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to rate',
        variant: 'destructive',
      });
    } finally {
      setIsRating(false);
    }
  };

  const handleAddComment = async () => {
  if (!newComment.trim() || newComment.trim().length < 10) {
    toast({
      title: 'Error',
      description: 'Comment must be at least 10 characters long',
      variant: 'destructive',
    });
    return;
  }
    if (!id || !newComment.trim() || isCommenting) return;
    setIsCommenting(true);
    try {
      const comment = await api.addComment(parseInt(id), newComment);
      setComments((prev) => [comment, ...(prev || [])]);
      setTotalComments((prev) => prev + 1);
      setNewComment('');
      toast({ title: 'Comment added' });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to add comment',
        variant: 'destructive',
      });
    } finally {
      setIsCommenting(false);
    }
  };

  const handleUpdateComment = async (commentId: number) => {
    if (!id || !editContent.trim()) return;
    try {
      const updated = await api.updateComment(parseInt(id), commentId, editContent);
      setComments((prev) =>
        prev.map((c) => (c.id === commentId ? updated : c))
      );
      setEditingComment(null);
      toast({ title: 'Comment updated' });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!id) return;
    try {
      await api.deleteComment(parseInt(id), commentId);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      setTotalComments((prev) => prev - 1);
      toast({ title: 'Comment deleted' });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete',
        variant: 'destructive',
      });
    }
  };

  const handleVote = async (commentId: number, vote: 'up' | 'down') => {
    if (!id) return;
    try {
      const result = await api.voteComment(parseInt(id), commentId, vote);
      setComments((prev) =>
        prev.map((c) =>
          c.id === commentId
            ? { ...c, upvotes: result.upvotes, downvotes: result.downvotes, user_vote: vote }
            : c
        )
      );
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to vote',
        variant: 'destructive',
      });
    }
  };

  const loadMoreComments = async () => {
    if (!id) return;
    try {
      const nextPage = commentsPage + 1;
      const data = await api.getComments(parseInt(id), nextPage * 10, 10);
      setComments((prev) => [...(prev || []), ...data.comments]);
      setCommentsPage(nextPage);
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to load more comments', variant: 'destructive' });
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </MainLayout>
    );
  }

  if (!tool) {
    return (
      <MainLayout>
        <div className="container mx-auto px-4 py-8 text-center">
          <h1 className="text-2xl font-bold mb-4">Tool not found</h1>
          <Link to="/dashboard">
            <Button variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </MainLayout>
    );
  }

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
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        {/* Back Button */}
        <Link to="/dashboard" className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Link>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Tool Info Card */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-2xl mb-2">{tool.name}</CardTitle>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant={getCategoryVariant(tool.category)}>{tool.category}</Badge>
                      <Badge variant={getStatusVariant(tool.status)}>{tool.status}</Badge>
                    </div>
                  </div>
                  <a href={tool.url} target="_blank" rel="noopener noreferrer">
                    <Button>
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Visit
                    </Button>
                  </a>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed mb-6">{tool.description}</p>
                <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    <span>by {tool.created_by}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>{format(new Date(tool.created_at), 'MMM d, yyyy')}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Comments Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="h-5 w-5" />
                  Comments ({totalComments})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Add Comment */}
                <div className="space-y-3">
                  <Textarea
                    placeholder="Share your thoughts about this tool..."
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    rows={3}
                  />
                  <Button
                    onClick={handleAddComment}
                    disabled={!newComment.trim() || isCommenting}
                  >
                    {isCommenting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    Post Comment
                  </Button>
                </div>

                <Separator />

                {/* Comments List */}
                {(!comments || comments.length === 0) ? (
                  <p className="text-center text-muted-foreground py-8">
                    No comments yet. Be the first to share your thoughts!
                  </p>
                ) : (
                  <div className="space-y-4">
                    {comments.map((comment) => (
                      <div key={comment.id} className="p-4 rounded-lg bg-muted/50">
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-full gradient-bg flex items-center justify-center">
                              <span className="text-xs font-medium text-primary-foreground">
                                {comment.username.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium text-sm">{comment.username}</p>
                              <p className="text-xs text-muted-foreground">
                                {format(new Date(comment.created_at), 'MMM d, yyyy')}
                              </p>
                            </div>
                          </div>
                          {user?.id === comment.user_id && (
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7"
                                onClick={() => {
                                  setEditingComment(comment.id);
                                  setEditContent(comment.content);
                                }}
                              >
                                <Pencil className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 text-destructive hover:text-destructive"
                                onClick={() => handleDeleteComment(comment.id)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          )}
                        </div>

                        {editingComment === comment.id ? (
                          <div className="space-y-2">
                            <Textarea
                              value={editContent}
                              onChange={(e) => setEditContent(e.target.value)}
                              rows={2}
                            />
                            <div className="flex gap-2">
                              <Button size="sm" onClick={() => handleUpdateComment(comment.id)}>
                                Save
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => setEditingComment(null)}
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <p className="text-sm mb-3">{comment.content}</p>
                        )}

                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => handleVote(comment.id, 'up')}
                            className={cn(
                              'flex items-center gap-1 text-xs transition-colors',
                              comment.user_vote === 'up'
                                ? 'text-success'
                                : 'text-muted-foreground hover:text-foreground'
                            )}
                          >
                            <ThumbsUp className="h-3 w-3" />
                            {comment.upvotes}
                          </button>
                          <button
                            onClick={() => handleVote(comment.id, 'down')}
                            className={cn(
                              'flex items-center gap-1 text-xs transition-colors',
                              comment.user_vote === 'down'
                                ? 'text-destructive'
                                : 'text-muted-foreground hover:text-foreground'
                            )}
                          >
                            <ThumbsDown className="h-3 w-3" />
                            {comment.downvotes}
                          </button>
                        </div>
                      </div>
                    ))}

                    {comments && comments.length < totalComments && (
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={loadMoreComments}
                      >
                        Load More Comments
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Rating */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="h-5 w-5 text-warning" />
                  Rating
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Average Rating */}
                <div className="text-center">
                  <div className="text-5xl font-bold mb-2">{tool.average_rating?.toFixed(1) || '0.0'}</div>
                  <StarRating rating={tool.average_rating} size="lg" />
                  <p className="text-sm text-muted-foreground mt-2">
                    Based on {tool.total_ratings} {tool.total_ratings === 1 ? 'rating' : 'ratings'}
                  </p>
                </div>

                <Separator />

                {/* Rating Distribution */}
                {tool.rating_distribution && (
                  <div className="space-y-2">
                    {[5, 4, 3, 2, 1].map((star) => {
                      const count = tool.rating_distribution?.[star] || 0;
                      const percentage = tool.total_ratings > 0 ? (count / tool.total_ratings) * 100 : 0;
                      return (
                        <div key={star} className="flex items-center gap-2">
                          <span className="text-sm w-3">{star}</span>
                          <Star className="h-3 w-3 fill-warning text-warning" />
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-warning rounded-full transition-all"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground w-8">{count}</span>
                        </div>
                      );
                    })}
                  </div>
                )}

                <Separator />

                {/* Your Rating */}
                <div>
                  <p className="text-sm font-medium mb-3">
                    {userRating ? 'Your rating' : 'Rate this tool'}
                  </p>
                  <StarRating
                    rating={userRating || 0}
                    size="lg"
                    interactive
                    onRate={handleRate}
                  />
                  {isRating && (
                    <p className="text-xs text-muted-foreground mt-2">Submitting...</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
