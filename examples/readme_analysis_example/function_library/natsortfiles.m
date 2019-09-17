function [X,ndx] = natsortfiles(X,varargin)
% Natural-order sort of a cell array of filenames/filepaths, with customizable numeric format.
%
% (c) 2015 Stephen Cobeldick
%
% Sort a cell array of filenames or filepaths, sorting the strings by both character
% order and the values of any numeric substrings that occur within the strings.
%
% Syntax:
%  Y = natsortfiles(X)
%  Y = natsortfiles(X,xpr)
%  Y = natsortfiles(X,xpr,<options>)
% [Y,ndx] = natsortfiles(X,...)
%
% The filenames and file extensions are sorted separately. This ensures that
% shorter filenames sort before longer (i.e. a dictionary sort). Note that
% a standard sort of filenames will sort any of char(0:45), including the
% characters [ !"#$%&'()*+,-], before the file extension character (period).
%
% Similarly the file separator character within filepaths can cause longer
% directory names to sort before short ones (char(0:46)<'/' and char(0:91)<'\').
% This submission splits filepaths at each file separator character and sorts
% every level of the directory hierarchy separately, ensuring that shorter
% directory names sort before longer, regardless of the characters in the names.
%
% Note: requires the function "natsort" (File Exchange 34464). All optional
%       inputs are passed directly to "natsort": see "natsort" for information
%       on case sensitivity, sort direction, and numeric substring matching.
%
% To sort all of the strings in a cell array use "natsort" (File Exchange 34464).
% To sort the rows of a cell array of strings use "natsortrows" (File Exchange 47433).
%
% See also NATSORT NATSORTROWS SORT SORTROWS SIPRE BIPRE CELLSTR REGEXP FILEPARTS FILESEP FULLFILE PWD DIR
%
% ### Examples ###
%
% A = {'test_x.m'; 'test-x.m'; 'test.m'};
% sort(A) % sorts '-' before '.'
%  ans = {
%     'test-x.m'
%     'test.m'
%     'test_x.m'}
% natsortfiles(A) % shorter names first (i.e. like a dictionary sort)
%  ans = {
%     'test.m'
%     'test-x.m'
%     'test_x.m'}
%
% B = {'test2.m'; 'test10-old.m'; 'test.m'; 'test10.m'; 'test1.m'};
% sort(B)
%  ans = {
%     'test.m'
%     'test1.m'
%     'test10-old.m'
%     'test10.m'
%     'test2.m'}
% natsortfiles(B) % correct numeric order and shortest first:
%  ans = {
%     'test.m'
%     'test1.m'
%     'test2.m'
%     'test10.m'
%     'test10-old.m'}
%
% C = {... % This is the order from the standard "sort" function:
%     'C:\Anna1\noise.mp10',...
%     'C:\Anna1\noise.mp3',...
%     'C:\Anna1\noise.mpX',...
%     'C:\Anna1archive.zip',...
%     'C:\Anna20\dir10\weigh.m',...
%     'C:\Anna20\dir1\weigh.m',...
%     'C:\Anna20\dir2\weigh.m',...
%     'C:\Anna3-all\archive.zip',...
%     'C:\Anna3\budget.pdf',...
%     'C:\Anna_archive.zip',...
%     'C:\Bob10\article.doc',...
%     'C:\Bob10_article.tex',...
%     'C:\Bob1\menu.png',...
%     'C:\Bob2\Work\test1.txt',...
%     'C:\Bob2\Work\test10.txt',...
%     'C:\Bob2\Work\test2.txt',...
%     'C:\info.log',...
%     'C:\info.txt',...
%     'C:\info1.log',...
%     'C:\info10.log',...
%     'C:\info2.log',...
%     'C:\info2.txt'};
% % Because '\' is treated as a character, a naive natural-order sort mixes
% % the subdirectory hierarchy, and longer directory names may come first:
% natsort(C)
%  ans = {
%     'C:\Anna1archive.zip'
%     'C:\Anna1\noise.mp3'
%     'C:\Anna1\noise.mp10'
%     'C:\Anna1\noise.mpX'
%     'C:\Anna3-all\archive.zip'
%     'C:\Anna3\budget.pdf'
%     'C:\Anna20\dir1\weigh.m'
%     'C:\Anna20\dir2\weigh.m'
%     'C:\Anna20\dir10\weigh.m'
%     'C:\Anna_archive.zip'
%     'C:\Bob1\menu.png'
%     'C:\Bob2\Work\test1.txt'
%     'C:\Bob2\Work\test2.txt'
%     'C:\Bob2\Work\test10.txt'
%     'C:\Bob10\article.doc'
%     'C:\Bob10_article.tex'
%     'C:\info.log'
%     'C:\info.txt'
%     'C:\info1.log'
%     'C:\info2.log'
%     'C:\info2.txt'
%     'C:\info10.log'}
% % This function sorts shorter directory names sort before longer (just
% % like a dictionary), and preserves the subdirectory hierarchy:
% natsortfiles(C)
%  ans = {
%     'C:\Anna1archive.zip'
%     'C:\Anna_archive.zip'
%     'C:\Bob10_article.tex'
%     'C:\info.log'
%     'C:\info.txt'
%     'C:\info1.log'
%     'C:\info2.log'
%     'C:\info2.txt'
%     'C:\info10.log'
%     'C:\Anna1\noise.mp3'
%     'C:\Anna1\noise.mp10'
%     'C:\Anna1\noise.mpX'
%     'C:\Anna3\budget.pdf'
%     'C:\Anna3-all\archive.zip'
%     'C:\Anna20\dir1\weigh.m'
%     'C:\Anna20\dir2\weigh.m'
%     'C:\Anna20\dir10\weigh.m'
%     'C:\Bob1\menu.png'
%     'C:\Bob2\Work\test1.txt'
%     'C:\Bob2\Work\test2.txt'
%     'C:\Bob2\Work\test10.txt'
%     'C:\Bob10\article.doc'}
%
% ### Input and Output Arguments ###
%
% Please see "natsort" for a full description of <xpr> and the <options>.
%
% Inputs (*=default):
%  X   = CellOfStrings, with filenames or filepaths to be sorted.
%  xpr = StringToken, regular expression to detect numeric substrings, '\d+'*.
%  <options> can be supplied in any order and are passed directly to "natsort".
%
% Outputs:
%  Y   = CellOfStrings, <X> with the filenames sorted according to <options>.
%  ndx = NumericMatrix, same size as <X>. Indices such that Y = X(ndx).
%
% [Y,ndx] = natsortrows(X,*xpr,<options>)

assert(iscellstr(X),'First input <X> must be a cell array of strings.')
%
% Split full filepaths into {path,name,extension}:
[pth,nam,ext] = cellfun(@fileparts,X(:),'UniformOutput',false);
% Split path into {root,subdir,subsubdir,...}
%pth = regexp(pth,filesep,'split'); % OS dependent
pth = regexp(pth,'[/\\]','split'); % either / or \
len = cellfun('length',pth);
vec(1:numel(len)) = {''};
%
% Natural-order sort of the extension, name and directories:
[~,ndx] = natsort(ext,varargin{:});
[~,ind] = natsort(nam(ndx),varargin{:});
ndx = ndx(ind);
for k = max(len):-1:1
    idx = len>=k;
    vec(~idx) = {''};
    vec(idx) = cellfun(@(c)c(k),pth(idx));
    [~,ind] = natsort(vec(ndx),varargin{:});
    ndx = ndx(ind);
end
%
% Return sorted array and indices:
ndx = reshape(ndx,size(X));
X = X(ndx);
%
end
%----------------------------------------------------------------------END:natsortfiles