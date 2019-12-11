function drawFix(dat,fixI2MC,res,img,missing,titel)

%% optional, if missing specified, remove missing from plotted 2D data
if isfield(dat,'left') && isfield(dat,'right')
    datx = [dat.left.X dat.right.X];
    daty = [dat.left.Y dat.right.Y];
else
    datx = dat.average.X;
    daty = dat.average.Y;
end
if nargin>4
    qMissL = datx==missing(1) & daty==missing(2);
    datx(qMissL) = nan;
    daty(qMissL) = nan;
end

%% configure axis positions
xpos = [0.1300 0.7673 0.7750 0.1577];
ypos = [0.1300 0.5482 0.7750 0.1577];
fixpos=[0.1300 0.1100 0.3347 0.3768];
rawpos=[0.5703 0.1100 0.3347 0.3768];

%% convert time everywhere such that t0=0 and time is in seconds
dat.time = dat.time./1000;
fixI2MC.startT = fixI2MC.startT./1000;
fixI2MC.endT   = fixI2MC.endT  ./1000;

%% 1D plots
[hx,hxr] = plotXT(xpos,dat.time,datx,res(1),false,'xpos',fixI2MC);
[hy,hyr] = plotXT(ypos,dat.time,daty,res(2),true ,'ypos',fixI2MC);


%% 2D plots
inr = struct('t',dat.time);
inf = struct('t',dat.time,'I2MC',fixI2MC);
% plot raw
rdat = {{1,inr,datx(:,1),daty(:,1),'b-'}};
if size(datx,2)>1
    rdat = {rdat{1}; {1,inr,datx(:,2),daty(:,2),'r-'}};
end
[hr,hrl] = plot2D(rawpos,res,img,[],rdat{:});
% plot fixations
rdat = {{1,inr,datx(:,1),daty(:,1),'Color',[.4 .4 1]}};
if size(datx,2)>1
    rdat = {rdat{1}; {1,inr,datx(:,2),daty(:,2),'Color',[1 .4 .4]}};
end
[hf,hfr,hfi] = plot2D(fixpos,res,img,{1,'raw'},...
    ... % draw very faint raw data first as background
    rdat{:},...
    ... % actual fixations, I2MC
    {2,inf,fixI2MC.xpos,fixI2MC.ypos,'b-','LineWidth',1.5},...
    {2,inf,fixI2MC.xpos,fixI2MC.ypos,'go','MarkerFaceColor','green','MarkerSize',4}...
    );

%% axes and data linking setup
% link time for x-t, y-t plots, link full view for 2D raw and fixation
% plots
linkaxes([hx hy],'x');
linkaxes([hr hf],'xy');
% link x-t time extents to data shown in 2D by setting up callbacks for
% actions that change the x-t, y-t axes
actions = {
    hx,[hrl hfr hfi];
    hy,[hrl hfr hfi];
};
set(zoom(gcf),'ActionPostCallback',@(obj,evd) viewCallbackFcn(obj,evd,actions));
set(pan(gcf) ,'ActionPostCallback',@(obj,evd) viewCallbackFcn(obj,evd,actions));

% set title. Below we'll add indication of which fix are currently shown
tit = title(hx,texlabel(titel,'literal'));

% make sure we don't lose the standard toolbar
set(gcf,'Toolbar','figure');
zoom on;
end


%%% helpers
function [h,hr] = plotXT(pos,time,xpos,res,qYRev,fixField,fixI2MC)
h = axes('position',pos); hold on
if qYRev
    h.YDir = 'reverse';
end
% draw eye data
hr = gobjects(1,2);
hr(1) = plot(time,xpos(:,1),'b-');
if size(xpos,2)>1
    hr(2) = plot(time,xpos(:,2),'r-');
end
% layout
ylabel('Horizontal position (pixels)');
xlabel('time (s)');
axis([time([1 end]).' 0 res]);
% add fixations
for b = 1:length(fixI2MC.startT)
    plot([fixI2MC.startT(b) fixI2MC.endT(b)],[fixI2MC.(fixField)(b) fixI2MC.(fixField)(b)],'k-','LineWidth',2);
end
end

function [h,hr,hi] = plot2D(pos,res,img,hidable,varargin)
h = axes('position',pos,'YDir','reverse'); hold on
if ~isempty(img)
    image('XData',img.x,'YData',img.y,'CData',img.data);
end

% prepare line output
idxs = cellfun(@(x) x{1},varargin);
assert(max(idxs)<=3)
hndls = cell(1,2);

% do plots
for p=1:length(varargin)
    pIdx = varargin{p}{1};
    % get axis
    if isempty(hndls{pIdx})
        hndls{pIdx} = hggroup();
        switch pIdx
            case 1
                hndls{pIdx}.Tag='raw';
            case 2
                hndls{pIdx}.Tag='fix';
        end
    end
    % do plot
    plot(varargin{p}{3:end},...
        'UserData',struct('info',varargin{p}{2},'x',varargin{p}{3},'y',varargin{p}{4}),...
        'Parent',hndls{pIdx});
end

% setup axis
xlabel('Horizontal position (pixels)');
ylabel('vertical position (pixels)');
axis([0 res(1) 0 res(2)]);

% add button enabling hiding of (part of) plots. hidable is index
% into plots indicating which should be hidable
if ~isempty(hidable)
    % toggle button raw data
    b=uicontrol(...
        'Style','pushbutton',...
        'String',['no ' hidable{2}],...
        'Units','Normalized',...
        'Position',[sum(pos([1 3]))+.01 sum(pos([2 4]))-.1 .04 .04],...
        'Callback',@(but,~,~) toggleVisible(but,hndls{hidable{1}},hidable{2}));% initial state, I2MC shown
toggleVisible(b,hndls{hidable{1}},hidable{2});
end

% prepare output
[hr,hi] = hndls{:};
end

% interaction
function viewCallbackFcn(~,evd,actions)
% get new view
newTLims = evd.Axes.XLim;
% for each defined action, see if the changed axis is among the ones the
% action listens for
for p=1:size(actions,1)
    if ismember(evd.Axes,actions{p,1})
        % yes, found an actions listening for change to this axis.
        % execute view change on defined targets
        for q=1:length(actions{p,2})
            tag = actions{p,2}(q).Tag;
            if strcmp(actions{p,2}(q).Type,'hggroup')
                hndls = actions{p,2}(q).Children;
            else
                hndls = actions{p,2}(q);
            end
            for l=1:length(hndls)
                dat = hndls(l).UserData;
                if isempty(dat)
                    continue;
                end
                if strcmp(tag,'raw')
                    qData = dat.info.t>=newTLims(1) & dat.info.t<=newTLims(2);
                    % grow visible by one sample so that connecting
                    % lines for samples just outside t lims are
                    % visible, just like they are in the xt plots
                    [on,off] = bool2bounds(qData);
                    on = max(1,on-1); off = min(off+1,length(dat.x));
                    % set plot data to new time limits
                    hndls(l).XData = dat.x(on:off).';
                    hndls(l).YData = dat.y(on:off).';
                else
                    % find all fixations that are partially visible
                    qData =  dat.info.I2MC.endT  >=newTLims(1) &  dat.info.I2MC.startT  <=newTLims(2);
                    % set plot data to new time limits
                    hndls(l).XData = dat.x(qData).';
                    hndls(l).YData = dat.y(qData).';
                end
            end
        end
    end
end
end

function toggleVisible(but,h,str)
if strcmpi(h.Visible,'on')
    h.Visible = 'off';
    but.String = str;
else
    h.Visible = 'on';
    but.String = ['no ' str];
end
end
