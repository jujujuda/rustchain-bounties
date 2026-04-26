import * as vscode from 'vscode';
import axios, { AxiosError } from 'axios';

interface RtcBalance { balance?: number; }
interface EpochInfo { epoch: number; slot: number; next_epoch_in?: number; }
interface BountyIssue { number: number; title: string; labels: string[]; }
interface GhLabel { name: string; }

class RustChainProvider {
  private nodeUrl: string = 'https://50.28.86.131';
  private walletName: string = '';
  private statusBar: vscode.StatusBarItem;
  private epochStatusBar: vscode.StatusBarItem;
  private refreshMs: number = 60000;
  private refreshTimer?: ReturnType<typeof setInterval>;

  constructor() {
    this.statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, Number.MAX_SAFE_INTEGER - 2);
    this.statusBar.command = 'rustchain.openWallet';
    this.statusBar.text = '$(diamond) RTC: --';

    this.epochStatusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, Number.MAX_SAFE_INTEGER);
    this.epochStatusBar.text = '$(clock) Epoch: --';

    this.loadConfig();
    this.setupCommands();
    this.startRefresh();
    this.statusBar.show();
    this.epochStatusBar.show();
  }

  private loadConfig() {
    const cfg = vscode.workspace.getConfiguration('rustchain');
    this.nodeUrl = cfg.get<string>('nodeUrl', 'https://50.28.86.131') || this.nodeUrl;
    this.walletName = cfg.get<string>('walletName', '') || '';
    this.refreshMs = ((cfg.get<number>('refreshInterval', 60)) || 60) * 1000;
    this.startRefresh();
  }

  private startRefresh() {
    if (this.refreshTimer) { clearInterval(this.refreshTimer); }
    this.refresh();
    this.refreshTimer = setInterval(() => this.refresh(), this.refreshMs);
  }

  private setupCommands() {
    vscode.commands.registerCommand('rustchain.refresh', () => this.refresh());
    vscode.commands.registerCommand('rustchain.openWallet', () => {
      if (this.walletName) {
        vscode.env.openExternal(vscode.Uri.parse(`https://rustchain.org/explorer/wallet/${this.walletName}`));
      }
    });
    vscode.commands.registerCommand('rustchain.openBounty', (_: any, issueNumber: number) => {
      vscode.env.openExternal(vscode.Uri.parse(`https://github.com/Scottcjn/rustchain-bounties/issues/${issueNumber}`));
    });
    vscode.workspace.onDidChangeConfiguration(() => this.loadConfig());
  }

  async refresh() {
    await Promise.allSettled([this.refreshBalance(), this.refreshEpoch()]);
  }

  async refreshBalance() {
    if (!this.walletName) {
      this.statusBar.text = '$(diamond) RTC: [set wallet]';
      this.statusBar.color = '#f0a030';
      return;
    }
    try {
      const { data } = await axios.get<RtcBalance>(
        `${this.nodeUrl}/wallet/balance`,
        { params: { miner_id: this.walletName }, timeout: 5000 }
      );
      const bal = data.balance ?? 0;
      this.statusBar.text = `$(diamond) RTC: ${bal.toFixed(2)}`;
      this.statusBar.color = bal > 0 ? '#30f030' : '#a0a0a0';
    } catch (_) {
      this.statusBar.text = '$(error) RTC: --';
      this.statusBar.color = '#f04040';
    }
  }

  async refreshEpoch() {
    try {
      const { data } = await axios.get<EpochInfo>(`${this.nodeUrl}/epoch`, { timeout: 5000 });
      const mins = Math.floor((data.next_epoch_in || 0) / 60);
      this.epochStatusBar.text = `$(clock) Ep${data.epoch} Slot${data.slot} ~${mins}m`;
    } catch (_) {
      this.epochStatusBar.text = '$(clock) Epoch: --';
    }
  }

  async getBounties(): Promise<BountyIssue[]> {
    const { data } = await axios.get<any[]>(
      'https://api.github.com/repos/Scottcjn/rustchain-bounties/issues',
      { params: { state: 'open', per_page: 100, labels: 'bounty' }, timeout: 10000 }
    );
    return data
      .filter(i => !i.pull_request)
      .map(i => ({ number: i.number, title: i.title, labels: (i.labels as GhLabel[] || []).map(l => l.name) }));
  }

  dispose() {
    if (this.refreshTimer) { clearInterval(this.refreshTimer); }
    this.statusBar.dispose();
    this.epochStatusBar.dispose();
  }
}

class BountyTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  constructor(private provider: RustChainProvider) {}

  async getChildren(): Promise<vscode.TreeItem[]> {
    try {
      const bounties = await this.provider.getBounties();
      if (!bounties.length) { return [new vscode.TreeItem('No open bounties')]; }
      return bounties.map(b => {
        const m = b.title.match(/(\d+)\s*RTC/i);
        const desc = m ? `${m[1]} RTC` : 'bounty';
        const item = new vscode.TreeItem(`#${b.number}  ${b.title}`);
        item.description = desc;
        item.iconPath = new vscode.ThemeIcon('gift');
        item.command = { command: 'rustchain.openBounty', title: 'Open Bounty', arguments: [b.number] };
        return item;
      });
    } catch (e) {
      return [new vscode.TreeItem(`Error: ${(e as Error).message}`)];
    }
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem { return element; }
}

export function activate(context: vscode.ExtensionContext) {
  const provider = new RustChainProvider();
  context.subscriptions.push(provider);
  context.subscriptions.push(vscode.window.registerTreeDataProvider('rustchain.bounties', new BountyTreeProvider(provider)));
  context.subscriptions.push(vscode.commands.registerCommand('rustchain.refresh', () => provider.refresh()));
}
